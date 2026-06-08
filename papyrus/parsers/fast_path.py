"""Fast path: lightweight parsing using pymupdf4llm and markitdown."""

import json
from pathlib import Path
from typing import Dict, Any

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False

try:
    import markitdown
    HAS_MARKITDOWN = True
except ImportError:
    HAS_MARKITDOWN = False


def parse_pdf_with_pymupdf4llm(file_path: str) -> str:
    """Parse PDF using pymupdf4llm (optimized for LLM consumption)."""
    if not HAS_PYMUPDF4LLM:
        raise ImportError("pymupdf4llm not installed. Run: pip install pymupdf4llm")

    md_text = pymupdf4llm.to_markdown(file_path)
    return md_text


def parse_with_markitdown(file_path: str) -> str:
    """Parse document using markitdown (supports PDF, DOCX, images, etc.)."""
    if not HAS_MARKITDOWN:
        raise ImportError("markitdown not installed. Run: pip install markitdown")

    converter = markitdown.MarkItDown()
    result = converter.convert(file_path)
    return result.text_content


def parse_with_fast_path(
    file_path: str,
    output_format: str = "markdown",
    use_markitdown: bool = False,
) -> Dict[str, Any]:
    """
    Parse file using fast path (lightweight parsers).

    Args:
        file_path: Path to the file
        output_format: "markdown" or "json"
        use_markitdown: Force use of markitdown instead of pymupdf4llm

    Returns:
        Dict with 'content' and 'format' keys
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Try pymupdf4llm for PDFs first (if not forced to markitdown)
    if path.suffix.lower() == ".pdf" and not use_markitdown:
        try:
            content = parse_pdf_with_pymupdf4llm(file_path)
        except Exception as e:
            # Fallback to markitdown
            content = parse_with_markitdown(file_path)
    else:
        content = parse_with_markitdown(file_path)

    if output_format == "json":
        return {
            "content": content,
            "format": "json",
            "metadata": {
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "parser": "pymupdf4llm" if path.suffix.lower() == ".pdf" and not use_markitdown else "markitdown",
            },
        }

    return {
        "content": content,
        "format": "markdown",
    }
