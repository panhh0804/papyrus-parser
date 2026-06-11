"""Command-line interface for Papyrus."""

import os
import sys
import json
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .cache import cache_info, cache_key, clear_cache, load_cached_result, store_cached_result
from .detector import detect_file_type, is_scanned_document
from .images import append_image_section, default_image_dir, extract_images
from .metadata import merge_metadata
from .router import route_file, get_path_reason
from .parsers.fast_path import parse_with_fast_path
from .parsers.heavy_path import parse_with_marker
from .settings import load_config
from .utils import echo, secho


def _do_parse(
    file_path: str,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
    verbose: bool,
) -> dict:
    """Inner parse routine without retry logic."""
    if output_format not in {"markdown", "json"}:
        raise ValueError(f"Unsupported output format: {output_format}")
    if force_heavy and force_fast:
        raise ValueError("Cannot use both --use-heavy and --use-fast")

    file_type = detect_file_type(file_path)
    if verbose:
        echo(f"📄 File: {file_path}", err=True)
        echo(f"📋 Type: {file_type}", err=True)

    route = route_file(file_path, force_heavy=force_heavy, force_fast=force_fast)
    if route == "unsupported":
        raise ValueError(f"Unsupported file type: {file_type}")
    if verbose:
        reason = get_path_reason(route, file_path)
        echo(f"🔄 {reason}", err=True)
    if route == "heavy":
        try:
            result = parse_with_marker(file_path, output_format=output_format)
        except ImportError as e:
            # Fallback to fast path if marker is not installed
            if force_heavy:
                secho(
                    "⚠️  Marker (OCR) unavailable, falling back to fast parser",
                    fg="yellow",
                    err=True,
                )
                echo(
                    f"   Reason: {str(e)[:80]}",
                    err=True,
                )
            elif verbose:
                secho(
                    "⚠️  Marker (OCR) unavailable, falling back to fast parser",
                    fg="yellow",
                    err=True,
                )
                echo(
                    f"   Reason: {str(e)[:80]}",
                    err=True,
                )
            result = parse_with_fast_path(file_path, output_format=output_format)
        except Exception as e:
            # Any other heavy-path failure (OOM, timeout, corrupt page) falls
            # back to fast path unless the user explicitly requested heavy.
            if force_heavy:
                raise
            if verbose:
                secho(
                    "⚠️  Heavy parser failed, falling back to fast parser...",
                    fg="yellow",
                    err=True,
                )
                echo(
                    f"   Reason: {str(e)[:80]}",
                    err=True,
                )
            result = parse_with_fast_path(file_path, output_format=output_format)
    else:
        result = parse_with_fast_path(file_path, output_format=output_format)
    return result
def _format_parse_error(file_path: str, original_err: Exception, retry_err: Exception) -> str:
    """Build a user-friendly error message for unrecoverable parse failures."""
    path = Path(file_path)
    try:
        size = path.stat().st_size
        size_str = f"{size} bytes ({size / 1024:.1f} KB)"
    except OSError:
        size_str = "unknown size"
    file_type = detect_file_type(file_path)
    return (
        f"Failed to parse {file_path}\n"
        f"  Detected type: {file_type}\n"
        f"  File size: {size_str}\n"
        f"  Original error: {original_err}\n"
        f"  Retry with fast parser also failed: {retry_err}\n\n"
        f"Suggestions:\n"
        f"  1. Check if the file opens correctly in a PDF viewer\n"
        f"  2. Re-download or re-copy the file if it might be incomplete\n"
        f"  3. Close other programs that may have the file open\n"
        f"  4. For password-protected PDFs, unlock them first\n"
        f"  5. Try --use-fast explicitly: papyrus \"{file_path}\" --use-fast"
    )
def parse_document(
    file_path: str,
    output_format: str = "markdown",
    force_heavy: bool = False,
    force_fast: bool = False,
    use_cache: Optional[bool] = None,
    extract_images_flag: bool = False,
    image_dir: Optional[str] = None,
    image_reference_dir: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Parse a document and return content.
    This function is used by both CLI and MCP server.
    Args:
        file_path: Path to the document
        output_format: Output format ("markdown" or "json")
        force_heavy: Force use of heavy parser
        force_fast: Force use of fast parser
        use_cache: Use content-addressed result cache
        extract_images_flag: Extract embedded images to disk
        image_dir: Directory for extracted images
        image_reference_dir: Directory used to build Markdown-relative paths
        verbose: Show detailed parsing information
    Returns:
        Dict with "content" and "format" keys
    Raises:
        FileNotFoundError: If file doesn't exist or isn't readable
        ValueError: For invalid parameters or unsupported file types
    """
    # Validate file exists and is readable
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file.is_file():
        raise ValueError(f"Not a file: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file (permission denied): {file_path}")
    if use_cache is None:
        use_cache = bool(load_config().get("cache", True))
    if use_cache:
        cached = load_cached_result(file_path, output_format, force_heavy, force_fast)
        if cached is not None:
            if verbose:
                echo("⚡ Cache hit", err=True)
            return _maybe_extract_images(
                cached,
                file_path,
                output_format,
                extract_images_flag,
                image_dir,
                image_reference_dir,
                verbose,
            )
    try:
        result = _do_parse(file_path, output_format, force_heavy, force_fast, verbose)
        result = merge_metadata(result, file_path)
        if use_cache:
            metadata = result.setdefault("metadata", {})
            metadata["cache_hit"] = False
            metadata["cache_key"] = cache_key(file_path, output_format, force_heavy, force_fast)
            store_cached_result(file_path, output_format, force_heavy, force_fast, result)
        return _maybe_extract_images(
            result,
            file_path,
            output_format,
            extract_images_flag,
            image_dir,
            image_reference_dir,
            verbose,
        )
    except Exception as first_err:
        err_msg = str(first_err)
        is_premature_close = "premature close" in err_msg.lower()
        is_stream_error = "stream" in err_msg.lower() and ("close" in err_msg.lower() or "read" in err_msg.lower())
        if (is_premature_close or is_stream_error) and not force_fast:
            if verbose:
                secho(
                    "⚠️  Parser failed with stream error, retrying with fast parser...",
                    fg="yellow",
                    err=True,
                )
            try:
                result = _do_parse(file_path, output_format, force_heavy, True, verbose)
                result = merge_metadata(result, file_path)
                if use_cache:
                    metadata = result.setdefault("metadata", {})
                    metadata["cache_hit"] = False
                    metadata["cache_key"] = cache_key(file_path, output_format, force_heavy, True)
                    store_cached_result(file_path, output_format, force_heavy, True, result)
                return _maybe_extract_images(
                    result,
                    file_path,
                    output_format,
                    extract_images_flag,
                    image_dir,
                    image_reference_dir,
                    verbose,
                )
            except Exception as retry_err:
                raise RuntimeError(
                    _format_parse_error(file_path, first_err, retry_err)
                ) from retry_err
        raise


def _maybe_extract_images(
    result: dict,
    file_path: str,
    output_format: str,
    extract_images_flag: bool,
    image_dir: Optional[str],
    image_reference_dir: Optional[str],
    verbose: bool,
) -> dict:
    """Attach extracted image assets to a parse result when requested."""
    if not extract_images_flag:
        return result

    target_dir = image_dir or str(default_image_dir(file_path))
    images = extract_images(file_path, target_dir, reference_dir=image_reference_dir)
    result.setdefault("assets", {})["images"] = images
    metadata = result.setdefault("metadata", {})
    metadata["images_extracted"] = len(images)
    metadata["image_dir"] = str(Path(target_dir).expanduser().resolve())
    if output_format == "markdown":
        result["content"] = append_image_section(result.get("content", ""), images)
    if verbose:
        echo(f"🖼 Extracted {len(images)} images to {metadata['image_dir']}", err=True)
    return result


@contextmanager
def _input_file_from_cli(file_path: str):
    """Yield a real file path, materializing stdin when file_path is '-'."""
    if file_path != "-":
        yield file_path
        return

    data = sys.stdin.buffer.read()
    if not data:
        raise ValueError("No data received on stdin")
    suffix = _stdin_suffix(data)
    tmp = tempfile.NamedTemporaryFile(prefix="papyrus-stdin-", suffix=suffix, delete=False)
    try:
        tmp.write(data)
        tmp.close()
        yield tmp.name
    finally:
        try:
            Path(tmp.name).unlink()
        except OSError:
            pass


def _stdin_suffix(data: bytes) -> str:
    """Choose a useful temporary suffix for stdin content."""
    if data.startswith(b"%PDF"):
        return ".pdf"
    try:
        data.decode("utf-8")
        return ".txt"
    except UnicodeDecodeError:
        return ".input"


def _output_text(result: dict, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    return result["content"]


def _write_or_echo(output_text: str, output: Optional[str], stdout: bool, verbose: bool) -> None:
    if output and not stdout:
        Path(output).write_text(output_text, encoding="utf-8")
        if verbose:
            echo(f"✅ Saved to: {output}", err=True)
    else:
        click.echo(output_text)


@click.command()
@click.argument("file_path", type=click.Path(exists=False))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json"]),
    default=None,
    help="Output format (markdown or json). Defaults to ~/.papyrus/config.toml or markdown.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (stdout if not specified)",
)
@click.option(
    "--stdout",
    is_flag=True,
    help="Force output to stdout even when --output is set",
)
@click.option(
    "--use-heavy",
    is_flag=True,
    help="Force use of heavy parser (marker with OCR)",
)
@click.option(
    "--use-fast",
    is_flag=True,
    help="Force use of fast parser (pymupdf4llm/markitdown)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed parsing information",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable the content-addressed parse cache for this run",
)
@click.option(
    "--extract-images",
    is_flag=True,
    help="Extract embedded PDF/PPTX/DOCX images to disk and add asset references",
)
@click.option(
    "--image-dir",
    type=click.Path(),
    default=None,
    help="Directory for --extract-images (default: <output>_images or <input>_images)",
)
def main(
    file_path: str,
    format: Optional[str],
    output: Optional[str],
    stdout: bool,
    use_heavy: bool,
    use_fast: bool,
    verbose: bool,
    no_cache: bool,
    extract_images: bool,
    image_dir: Optional[str],
):
    """
    Parse documents to markdown or JSON.

    Automatically routes to fast (pymupdf4llm/markitdown) or heavy (marker) parser
    based on document characteristics. Supports PDFs, DOCX, and more.

    Examples:
        papyrus homework.pdf
        papyrus report.pdf --format json --output result.json
        papyrus scanned_document.pdf --use-heavy
    """
    try:
        config = load_config()
        output_format = format or config["format"]
        with _input_file_from_cli(file_path) as real_path:
            resolved_image_dir = image_dir
            if extract_images and resolved_image_dir is None:
                resolved_image_dir = str(default_image_dir(real_path, output))
            image_reference_dir = str(Path(output).parent) if output else str(Path.cwd())
            result = parse_document(
                real_path,
                output_format=output_format,
                force_heavy=use_heavy,
                force_fast=use_fast,
                use_cache=not no_cache,
                extract_images_flag=extract_images,
                image_dir=resolved_image_dir,
                image_reference_dir=image_reference_dir,
                verbose=verbose,
            )

        _write_or_echo(_output_text(result, output_format), output, stdout, verbose)

    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    except ImportError as e:
        click.secho(f"Error: {e}", fg="yellow", err=True)
        click.echo(
            "\nTo fix, install missing dependencies:\n"
            "  pip install papyrus\n"
            "  pip install 'papyrus[heavy]'  # for marker support",
            err=True,
        )
        sys.exit(1)

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        if verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


@click.group()
@click.version_option(version=__version__, prog_name="papyrus")
def cli():
    """Papyrus - Universal document parser for AI agents."""
    pass


@cli.group("cache")
def cache_cmd():
    """Inspect or clear Papyrus parse cache."""
    pass


@cache_cmd.command("info")
def cache_info_cmd():
    """Show cache location, entries, and size."""
    info = cache_info()
    click.echo(json.dumps(info, ensure_ascii=False, indent=2))


@cache_cmd.command("clear")
def cache_clear_cmd():
    """Delete all cached parse results."""
    info = clear_cache()
    secho(
        f"Cleared {info['entries']} cache entries from {info['cache_dir']}",
        fg="green",
    )


@cli.command("mcp")
def run_mcp():
    """Run Papyrus as an MCP (Model Context Protocol) server."""
    try:
        from .mcp_server import run_mcp_server
        run_mcp_server()
    except ImportError:
        click.secho(
            "Error: MCP server requires additional dependencies",
            fg="red",
            err=True,
        )
        sys.exit(1)


@cli.command("setup")
@click.argument(
    "tool",
    type=click.Choice(
        ["all", "claude-code", "codex", "kimi", "agents-md"],
        case_sensitive=False,
    ),
    required=False,
)
@click.option(
    "--mcp",
    is_flag=True,
    help="Use MCP (Model Context Protocol) server instead of SKILL.md",
)
def setup_tools(tool: Optional[str], mcp: bool):
    """Set up Papyrus configuration for AI tools.

    \b
    Examples:
        papyrus setup                  # Interactive menu
        papyrus setup all              # Set up all tools
        papyrus setup claude-code      # Set up only Claude Code
        papyrus setup all --mcp        # Use MCP for all tools
    """
    from .config_manager import ConfigManager

    manager = ConfigManager()

    if not tool:
        # Interactive menu
        tool = click.prompt(
            "Which tool to set up?",
            type=click.Choice(["all", "claude-code", "codex", "kimi", "agents-md"]),
            default="all",
        )

        if not mcp:
            mcp = click.confirm(
                "Use MCP (Model Context Protocol) server? (recommended)",
                default=True,
            )

    # Check if any existing configs are outdated
    outdated = manager.check_all_configs()
    if outdated:
        click.echo("")
        secho(
            "⚠️  Some config files are outdated and will be updated:",
            fg="yellow",
            bold=True,
        )
        for name in outdated:
            click.echo(f"   - {name}")
        click.echo("")

    click.echo("")
    secho("🔧 Setting up Papyrus...", fg="cyan", bold=True)
    click.echo("")

    success_count = 0
    total_count = 0

    tools_to_setup = {
        "claude-code": lambda: manager.setup_claude_code(mcp_mode=mcp),
        "codex": lambda: manager.setup_codex(mcp_mode=mcp),
        "kimi": lambda: manager.setup_kimi(mcp_mode=mcp),
        "agents-md": lambda: manager.setup_agents_md(),
    }

    if tool == "all":
        for tool_name, setup_func in tools_to_setup.items():
            total_count += 1
            if setup_func():
                success_count += 1
    elif tool == "agents-md":
        total_count += 1
        if manager.setup_agents_md():
            success_count += 1
    else:
        total_count += 1
        if tools_to_setup[tool]():
            success_count += 1

    click.echo("")
    click.secho("=" * 60, fg="cyan")

    if success_count == total_count:
        secho("✅ Setup completed successfully!", fg="green", bold=True)
    else:
        secho(
            f"⚠️  Setup partially completed ({success_count}/{total_count})",
            fg="yellow",
            bold=True,
        )

    click.echo("")
    click.echo("Next steps:")
    click.echo("")

    if mcp:
        click.echo("1. Start Papyrus MCP server:")
        click.echo("   python -m papyrus.mcp_server")
        click.echo("")
        click.echo("2. Restart your AI tool (Claude Code, Codex, etc.)")
        click.echo("")
        click.echo("3. Ask your tool to read a document - it should automatically")
        click.echo("   use the parse_document tool from Papyrus MCP server")
        click.echo("")
        secho("📚 See MCP_SETUP.md for detailed MCP configuration", fg="cyan")
    else:
        click.echo("1. Restart your AI tool (Claude Code, Codex, etc.)")
        click.echo("")
        click.echo("2. Ask your tool to read a document - it should automatically")
        click.echo("   know to use Papyrus")
        click.echo("")

    click.echo("")
    secho("💡 Tip: Run 'papyrus setup --help' to see all options", fg="cyan")
    click.echo("")


def _parse_one_file(
    input_path: Path,
    output_path: Path,
    log_path: Path,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
    use_cache: bool,
    extract_images_flag: bool,
) -> tuple[str, bool]:
    """Parse a single file and save output/log. Returns (file_name, success)."""
    try:
        result = parse_document(
            str(input_path),
            output_format=output_format,
            force_heavy=force_heavy,
            force_fast=force_fast,
            use_cache=use_cache,
            extract_images_flag=extract_images_flag,
            image_dir=str(output_path.parent / f"{output_path.name}_images"),
            image_reference_dir=str(output_path.parent),
            verbose=False,
        )

        if output_format == "json":
            output_text = json.dumps(result, ensure_ascii=False, indent=2)
            output_path = output_path.with_suffix(".json")
        else:
            output_text = result["content"]
            output_path = output_path.with_suffix(".md")

        output_path.write_text(output_text, encoding="utf-8")
        return (input_path.name, True)
    except Exception as e:
        error_text = f"Error parsing {input_path}:\n\n{type(e).__name__}: {e}\n\n"
        error_text += traceback.format_exc()
        log_path.write_text(error_text, encoding="utf-8")
        return (input_path.name, False)


@cli.command("batch")
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: ./papyrus-output)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json"]),
    default=None,
    help="Output format (markdown or json). Defaults to ~/.papyrus/config.toml or markdown.",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count or 4)",
)
@click.option(
    "--executor",
    type=click.Choice(["threads", "processes"]),
    default=None,
    help="Parallel executor for batch mode. Processes help CPU-heavy OCR workloads.",
)
@click.option(
    "--use-heavy",
    is_flag=True,
    help="Force use of heavy parser (marker with OCR)",
)
@click.option(
    "--use-fast",
    is_flag=True,
    help="Force use of fast parser (pymupdf4llm/markitdown)",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively process subdirectories",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable parse cache for batch items",
)
@click.option(
    "--extract-images",
    is_flag=True,
    help="Extract embedded PDF/PPTX/DOCX images beside each parsed output",
)
def batch_cmd(
    input_dir: Path,
    output_dir: Optional[Path],
    format: Optional[str],
    workers: Optional[int],
    executor: Optional[str],
    use_heavy: bool,
    use_fast: bool,
    recursive: bool,
    no_cache: bool,
    extract_images: bool,
):
    """Batch parse all documents in a directory.

    Automatically discovers PDF, PPTX, DOCX, XLSX, HTML, Markdown, and text files.
    Parses them in parallel and writes outputs to the output directory.
    Errors are saved to individual .log files.

    \b
    Examples:
        papyrus batch ./lectures
        papyrus batch ./lectures -o ./output --workers 4
        papyrus batch ./lectures --use-fast -r
    """
    config = load_config()
    output_format = format or config["format"]
    executor_name = executor or config["batch_executor"]
    supported_exts = {
        ".pdf", ".pptx", ".docx", ".xlsx", ".html", ".htm",
        ".md", ".markdown", ".txt", ".text",
    }

    # Collect files
    if recursive:
        files = sorted(
            p for p in input_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in supported_exts
        )
    else:
        files = sorted(
            p for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in supported_exts
        )

    if not files:
        secho("No supported documents found.", fg="yellow", err=True)
        sys.exit(1)

    # Default output directory
    if output_dir is None:
        output_dir = Path.cwd() / "papyrus-output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine workers
    if workers is None:
        workers = config.get("workers") or min(4, os.cpu_count() or 4)
    workers = max(1, workers)

    total = len(files)
    success_count = 0
    fail_count = 0

    secho(
        f"📦 Batch parsing {total} files with {workers} {executor_name} workers...",
        fg="cyan",
        bold=True,
        err=True,
    )
    click.echo("", err=True)

    executor_cls = ProcessPoolExecutor if executor_name == "processes" else ThreadPoolExecutor
    with executor_cls(max_workers=workers) as pool:
        future_to_file = {}
        for file_path in files:
            # Preserve relative directory structure under output_dir
            try:
                rel_path = file_path.relative_to(input_dir)
            except ValueError:
                rel_path = file_path.name

            out_file = output_dir / rel_path.with_suffix("")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            log_file = out_file.with_suffix(".log")

            future = pool.submit(
                _parse_one_file,
                file_path,
                out_file,
                log_file,
                output_format,
                use_heavy,
                use_fast,
                not no_cache,
                extract_images,
            )
            future_to_file[future] = (file_path, out_file, log_file)

        for future in as_completed(future_to_file):
            file_path, out_file, log_file = future_to_file[future]
            name, success = future.result()

            if success:
                success_count += 1
                echo(f"✅ [{success_count + fail_count}/{total}] {name}", err=True)
            else:
                fail_count += 1
                secho(
                    f"❌ [{success_count + fail_count}/{total}] {name} (see {log_file.name})",
                    fg="red",
                    err=True,
                )

    click.echo("", err=True)
    click.secho("=" * 60, fg="cyan", err=True)
    secho(
        f"📊 Done: {success_count} succeeded, {fail_count} failed out of {total}",
        fg="green" if fail_count == 0 else "yellow",
        bold=True,
        err=True,
    )
    secho(f"📁 Output directory: {output_dir}", fg="cyan", err=True)

    if fail_count > 0:
        sys.exit(1)


# Add the parse command to the group
cli.add_command(main, name="parse")
cli.add_command(batch_cmd, name="batch")


def run_cli():
    """Entry point with default command support.

    If the first positional argument is not a known sub-command,
    automatically prepend 'parse' so `papyrus <file>` works.
    """
    import sys

    if len(sys.argv) > 1:
        first = sys.argv[1]
        # Known sub-commands + common flags that should not trigger default
        known = {"parse", "batch", "setup", "mcp", "cache", "--help", "-h", "--version"}
        if (first == "-" or not first.startswith("-")) and first not in known:
            sys.argv.insert(1, "parse")

    cli()


if __name__ == "__main__":
    run_cli()
