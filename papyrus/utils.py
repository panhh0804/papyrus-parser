"""Utility functions for cross-platform compatibility."""

import sys


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def echo(msg: str, **kwargs) -> None:
    """Print a message, stripping emoji on Windows to avoid terminal crashes."""
    import click
    if is_windows():
        msg = _strip_emoji(msg)
    click.echo(msg, **kwargs)


def secho(msg: str, **kwargs) -> None:
    """Styled print, stripping emoji on Windows to avoid terminal crashes."""
    import click
    if is_windows():
        msg = _strip_emoji(msg)
    click.secho(msg, **kwargs)


def _strip_emoji(text: str) -> str:
    """Replace common emoji and non-ASCII symbols with ASCII equivalents."""
    replacements = {
        "📄": "[File]",
        "📋": "[Type]",
        "🔄": "[Router]",
        "⚠️": "[WARN]",
        "✅": "[OK]",
        "🔧": "[Setup]",
        "📚": "[Docs]",
        "💡": "[Tip]",
        "❌": "[FAIL]",
        "✓": "[OK]",
        "✗": "[FAIL]",
        "⚠": "[WARN]",
        "ℹ": "[INFO]",
        "—": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
    }
    for emoji, ascii_text in replacements.items():
        text = text.replace(emoji, ascii_text)
    # Strip remaining characters outside the BMP or common emoji ranges
    # by encoding to ASCII with ignore, but preserve printable chars > 127
    # that might be in document content.
    # For CLI messages we simply drop anything non-ASCII after replacements.
    result = []
    for ch in text:
        cp = ord(ch)
        if cp <= 127:
            result.append(ch)
        else:
            # if it's a known replacement we already handled, else skip
            pass
    return "".join(result)


def print_compat(msg: str) -> None:
    """Print message with emoji stripped on Windows."""
    if is_windows():
        msg = _strip_emoji(msg)
    print(msg)
