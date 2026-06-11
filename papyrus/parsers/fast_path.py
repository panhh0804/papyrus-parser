"""Fast path: lightweight parsing using pymupdf4llm and markitdown."""

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from ..detector import detect_file_type

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import markitdown
    HAS_MARKITDOWN = True
except ImportError:
    HAS_MARKITDOWN = False


@contextlib.contextmanager
def _suppress_library_stdout():
    """Suppress noisy Python and C-level stdout from third-party parsers."""
    sys_stdout = io.StringIO()
    saved_fd = os.dup(1)
    try:
        with tempfile.TemporaryFile(mode="w+b") as tmp:
            os.dup2(tmp.fileno(), 1)
            with contextlib.redirect_stdout(sys_stdout):
                yield
    finally:
        os.dup2(saved_fd, 1)
        os.close(saved_fd)


def parse_pdf_with_pymupdf4llm(file_path: str) -> str:
    """Parse PDF using pymupdf4llm (optimized for LLM consumption)."""
    if not HAS_PYMUPDF4LLM:
        raise ImportError("pymupdf4llm not installed. Run: pip install pymupdf4llm")

    with _suppress_library_stdout():
        md_text = pymupdf4llm.to_markdown(file_path)
    return md_text


def parse_pdf_with_fitz_raw(file_path: str) -> str:
    """Parse PDF using raw PyMuPDF fitz API (stable fallback for large files)."""
    if not HAS_FITZ:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    doc = fitz.open(file_path)
    try:
        pages = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            if text:
                pages.append(f"## Page {page_num}\n\n{text}")
        return "\n\n".join(pages) if pages else ""
    finally:
        doc.close()


def parse_with_markitdown(file_path: str) -> str:
    """Parse document using markitdown (supports PDF, DOCX, images, etc.)."""
    if not HAS_MARKITDOWN:
        raise ImportError("markitdown not installed. Run: pip install markitdown")

    converter = markitdown.MarkItDown()
    with _suppress_library_stdout():
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
    if output_format not in {"markdown", "json"}:
        raise ValueError(f"Unsupported output format: {output_format}")

    parser_used = "markitdown"
    suffix = path.suffix.lower()
    file_type = detect_file_type(str(path))

    if file_type in {"markdown", "txt"}:
        content = path.read_text(encoding="utf-8", errors="replace")
        parser_used = "text"
    # Try pymupdf4llm for PDFs first (if not forced to markitdown)
    elif file_type == "pdf" and not use_markitdown:
        try:
            content = parse_pdf_with_pymupdf4llm(file_path)
            parser_used = "pymupdf4llm"
        except Exception:
            # Fallback 1: raw PyMuPDF (more stable for large / tricky PDFs)
            try:
                content = parse_pdf_with_fitz_raw(file_path)
                parser_used = "pymupdf-raw"
            except Exception:
                # Fallback 2: markitdown
                content = parse_with_markitdown(file_path)
                parser_used = "markitdown"
    else:
        content = parse_with_markitdown(file_path)

    if output_format == "json":
        return {
            "content": content,
            "format": "json",
            "metadata": {
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "parser": parser_used,
            },
        }

    return {
        "content": content,
        "format": "markdown",
    }
