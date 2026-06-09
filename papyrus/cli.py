"""Command-line interface for Papyrus."""

import os
import sys
import json
from pathlib import Path
from typing import Optional

import click

from .detector import detect_file_type, is_scanned_document
from .router import route_file, get_path_reason
from .parsers.fast_path import parse_with_fast_path
from .parsers.heavy_path import parse_with_marker
from .utils import echo, secho


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
        verbose: Show detailed information

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

    # Detect file type
    file_type = detect_file_type(file_path)

    if verbose:
        echo(f"📄 File: {file_path}", err=True)
        echo(f"📋 Type: {file_type}", err=True)

    # Validate parameters
    if force_heavy and force_fast:
        raise ValueError("Cannot use both --use-heavy and --use-fast")

    route = route_file(file_path, force_heavy=force_heavy, force_fast=force_fast)

    if route == "unsupported":
        raise ValueError(f"Unsupported file type: {file_type}")

    if verbose:
        reason = get_path_reason(route, file_path)
        echo(f"🔄 {reason}", err=True)

    # Parse
    if route == "heavy":
        try:
            result = parse_with_marker(file_path, output_format=output_format)
        except ImportError as e:
            # Fallback to fast path if marker is not installed
            if force_heavy:
                # Always warn when user explicitly requested --use-heavy
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
    else:
        result = parse_with_fast_path(file_path, output_format=output_format)

    return result


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


# Add the parse command to the group
cli.add_command(main, name="parse")


def run_cli():
    """Entry point with default command support.

    If the first positional argument is not a known sub-command,
    automatically prepend 'parse' so `papyrus <file>` works.
    """
    import sys

    if len(sys.argv) > 1:
        first = sys.argv[1]
        # Known sub-commands + common flags that should not trigger default
        known = {"parse", "setup", "mcp", "--help", "-h", "--version"}
        if not first.startswith("-") and first not in known:
            sys.argv.insert(1, "parse")

    cli()


if __name__ == "__main__":
    run_cli()
