"""Command-line interface for Papyrus."""

import os
import sys
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import click

from .detector import detect_file_type, is_scanned_document
from .router import route_file, get_path_reason
from .parsers.fast_path import parse_with_fast_path
from .parsers.heavy_path import parse_with_marker
from .utils import echo, secho


def _do_parse(
    file_path: str,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
    verbose: bool,
) -> dict:
    """Inner parse routine without retry logic."""
    file_type = detect_file_type(file_path)
    if verbose:
        echo(f"📄 File: {file_path}", err=True)
        echo(f"📋 Type: {file_type}", err=True)
    if force_heavy and force_fast:
        raise ValueError("Cannot use both --use-heavy and --use-fast")
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
    try:
        return _do_parse(file_path, output_format, force_heavy, force_fast, verbose)
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
                return _do_parse(file_path, output_format, force_heavy, True, verbose)
            except Exception as retry_err:
                raise RuntimeError(
                    _format_parse_error(file_path, first_err, retry_err)
                ) from retry_err
        raise
@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format (markdown or json)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (stdout if not specified)",
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
def main(
    file_path: str,
    format: str,
    output: Optional[str],
    use_heavy: bool,
    use_fast: bool,
    verbose: bool,
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
        result = parse_document(
            file_path,
            output_format=format,
            force_heavy=use_heavy,
            force_fast=use_fast,
            verbose=verbose,
        )

        # Output
        if format == "json":
            output_text = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            output_text = result["content"]

        if output:
            Path(output).write_text(output_text, encoding="utf-8")
            if verbose:
                echo(f"✅ Saved to: {output}", err=True)
        else:
            click.echo(output_text)

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
def cli():
    """Papyrus - Universal document parser for AI agents."""
    pass


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
) -> tuple[str, bool]:
    """Parse a single file and save output/log. Returns (file_name, success)."""
    try:
        result = parse_document(
            str(input_path),
            output_format=output_format,
            force_heavy=force_heavy,
            force_fast=force_fast,
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
    default="markdown",
    help="Output format (markdown or json)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count or 4)",
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
def batch_cmd(
    input_dir: Path,
    output_dir: Optional[Path],
    format: str,
    workers: Optional[int],
    use_heavy: bool,
    use_fast: bool,
    recursive: bool,
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
    supported_exts = {
        ".pdf", ".pptx", ".docx", ".xlsx", ".html", ".htm",
        ".md", ".markdown", ".txt",
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
        workers = min(4, os.cpu_count() or 4)
    workers = max(1, workers)

    total = len(files)
    success_count = 0
    fail_count = 0

    secho(f"📦 Batch parsing {total} files with {workers} workers...", fg="cyan", bold=True, err=True)
    click.echo("", err=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
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

            future = executor.submit(
                _parse_one_file,
                file_path,
                out_file,
                log_file,
                format,
                use_heavy,
                use_fast,
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
        known = {"parse", "batch", "setup", "mcp", "--help", "-h", "--version"}
        if not first.startswith("-") and first not in known:
            sys.argv.insert(1, "parse")

    cli()


if __name__ == "__main__":
    run_cli()
