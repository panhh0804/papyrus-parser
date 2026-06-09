"""Command-line interface for Papyrus."""

import sys
import json
from pathlib import Path
from typing import Optional

import click

from .detector import detect_file_type, is_scanned_document
from .router import route_file, get_path_reason
from .parsers.fast_path import parse_with_fast_path
from .parsers.heavy_path import parse_with_marker


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
    """
    # Detect file type
    file_type = detect_file_type(file_path)

    if verbose:
        click.echo(f"📄 File: {file_path}", err=True)
        click.echo(f"📋 Type: {file_type}", err=True)

    # Route to appropriate parser
    if force_heavy and force_fast:
        raise ValueError("Cannot use both --use-heavy and --use-fast")

    route = route_file(file_path, force_heavy=force_heavy, force_fast=force_fast)

    if route == "unsupported":
        raise ValueError(f"Unsupported file type: {file_type}")

    if verbose:
        reason = get_path_reason(route, file_path)
        click.echo(f"🔄 {reason}", err=True)

    # Parse
    if route == "heavy":
        try:
            result = parse_with_marker(file_path, output_format=output_format)
        except ImportError:
            # Fallback to fast path if marker is not installed
            if verbose:
                click.echo(
                    f"⚠️  Heavy path unavailable, falling back to fast path",
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
                click.echo(f"✅ Saved to: {output}", err=True)
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


# Add the parse command to the group
cli.add_command(main, name="parse")

# Keep the old interface for backwards compatibility
if __name__ == "__main__":
    # If called directly without subcommand, default to parse
    if len(sys.argv) > 1 and sys.argv[1] not in ["mcp", "--help", "-h"]:
        # This is a parse command, use main directly
        main()
    else:
        # Use the group with subcommands
        cli()
