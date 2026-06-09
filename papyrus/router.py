"""Route files to appropriate parsing strategy."""

from typing import Literal
from .detector import detect_file_type, should_use_heavy_path


def route_file(
    file_path: str,
    force_heavy: bool = False,
    force_fast: bool = False,
) -> Literal["fast", "heavy", "unsupported"]:
    """
    Route file to fast or heavy parsing path.

    Args:
        file_path: Path to the file
        force_heavy: Force use of heavy path (marker)
        force_fast: Force use of fast path

    Returns:
        "fast": Use pymupdf4llm/markitdown (quick, lightweight)
        "heavy": Use marker (slower, better for complex docs)
        "unsupported": File type not supported
    """
    if force_heavy:
        return "heavy"

    if force_fast:
        return "fast"

    file_type = detect_file_type(file_path)

    # Unsupported formats
    unsupported = {"unknown", "ppt"}
    if file_type in unsupported:
        return "unsupported"

    # Non-PDF files always use fast path
    if file_type != "pdf":
        return "fast"

    # PDFs: decide based on content characteristics
    if should_use_heavy_path(file_path):
        return "heavy"

    return "fast"


def get_path_reason(route: str, file_path: str) -> str:
    """Get human-readable reason for routing decision."""
    file_type = detect_file_type(file_path)

    if route == "unsupported":
        return "Unsupported file type"

    if route == "heavy":
        return "Complex/scanned PDF - using heavy parser (marker with OCR)"

    fast_reasons = {
        "pdf": "Light PDF - using fast parser (pymupdf4llm)",
        "docx": "Word document - using fast parser (markitdown)",
        "doc": "Word document - using fast parser (markitdown)",
        "pptx": "PowerPoint - using fast parser (markitdown)",
        "html": "HTML page - using fast parser (markitdown)",
        "excel": "Excel spreadsheet - using fast parser (markitdown)",
        "markdown": "Markdown file - using fast parser",
        "txt": "Text file - using fast parser",
    }
    return fast_reasons.get(file_type, f"{file_type.upper()} file - using fast parser (markitdown)")
