"""File type and content detection."""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple

try:
    import fitz  # pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


def detect_file_type(file_path: str) -> str:
    """
    Detect file type by extension and mimetype.

    Returns: 'pdf', 'docx', 'doc', 'markdown', 'txt', or 'unknown'
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    # Direct extension mapping
    ext_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.txt': 'txt',
        '.html': 'html',
        '.htm': 'html',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.pptx': 'pptx',
        '.ppt': 'ppt',
    }

    if ext in ext_map:
        return ext_map[ext]

    # Fallback to mimetype
    mime, _ = mimetypes.guess_type(file_path)
    if mime:
        if 'pdf' in mime:
            return 'pdf'
        if 'word' in mime or 'document' in mime:
            return 'docx'
        if 'text' in mime:
            return 'txt'

    return 'unknown'


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB."""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def is_scanned_pdf(file_path: str) -> bool:
    """
    Detect if PDF is scanned (image-based, no selectable text).

    Returns True if text extraction ratio is very low (< 10% text content).
    Threshold: average < 50 characters per page indicates scanned PDF.
    """
    if not HAS_PYMUPDF:
        return False

    doc = None
    try:
        doc = fitz.open(file_path)
        total_chars = 0
        total_pages = len(doc)

        for page in doc:
            text = page.get_text()
            total_chars += len(text.strip())

        # If < 50 chars/page on average, likely scanned
        avg_chars_per_page = total_chars / max(1, total_pages)
        is_scanned = avg_chars_per_page < 50
        return is_scanned
    except Exception:
        return False
    finally:
        if doc is not None:
            doc.close()


def is_complex_pdf(file_path: str) -> bool:
    """
    Detect if PDF has complex layout (tables, figures, mixed content).

    Returns True if:
    - PDF has > 50 pages (typically complex)
    - Any page has > 2 images (indicates figures/tables)
    - Any page has > 20 text blocks (indicates complex layout)
    """
    if not HAS_PYMUPDF:
        return False

    doc = None
    try:
        doc = fitz.open(file_path)
        # Long PDFs are often complex
        if len(doc) > 50:
            return True

        for page in doc:
            # Check for images, paths (drawings), multiple text blocks
            image_count = len(page.get_images())
            blocks = page.get_text("blocks")

            # Thresholds: 2+ images or 20+ text blocks = complex
            if image_count > 2 or len(blocks) > 20:
                return True

        return False
    except Exception:
        return False
    finally:
        if doc is not None:
            doc.close()


def is_scanned_document(file_path: str) -> bool:
    """Check if document is scanned/image-based."""
    file_type = detect_file_type(file_path)

    if file_type == 'pdf':
        return is_scanned_pdf(file_path)

    # For now, assume other formats are not scanned
    return False


def should_use_heavy_path(file_path: str) -> bool:
    """
    Decide if file should use heavy (marker) path.

    Criteria:
    - Scanned PDFs (need OCR)
    - Large PDFs with complex layout
    - Explicitly requested
    """
    file_type = detect_file_type(file_path)

    if file_type != 'pdf':
        return False

    if is_scanned_pdf(file_path):
        return True

    if is_complex_pdf(file_path):
        return True

    return False
