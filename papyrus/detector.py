"""File type and content detection."""

import os
import mimetypes
from pathlib import Path

try:
    import fitz  # pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


EXTENSION_MAP = {
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.doc': 'doc',
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.txt': 'txt',
    '.text': 'txt',
    '.html': 'html',
    '.htm': 'html',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.pptx': 'pptx',
    '.ppt': 'ppt',
}


def detect_file_type(file_path: str) -> str:
    """
    Detect file type by extension and mimetype.

    Returns: 'pdf', 'docx', 'doc', 'markdown', 'txt', or 'unknown'
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]

    # Fallback to libmagic when the extension is missing or unfamiliar.
    if HAS_MAGIC:
        try:
            magic_mime = magic.from_file(str(path), mime=True)
            detected = _type_from_mime(magic_mime)
            if detected != "unknown":
                return detected
        except Exception:
            pass

    # Last fallback to Python's mimetype table.
    mime, _ = mimetypes.guess_type(file_path)
    if mime:
        return _type_from_mime(mime)

    return 'unknown'


def _type_from_mime(mime: str) -> str:
    """Map a MIME type to Papyrus' internal file type names."""
    mime = (mime or "").lower()
    if 'pdf' in mime:
        return 'pdf'
    if 'presentation' in mime or 'powerpoint' in mime:
        return 'pptx'
    if 'spreadsheet' in mime or 'excel' in mime:
        return 'excel'
    if 'word' in mime or 'document' in mime:
        return 'docx'
    if 'html' in mime:
        return 'html'
    if 'markdown' in mime:
        return 'markdown'
    if mime.startswith('text/'):
        return 'txt'
    return 'unknown'


def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB."""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def is_scanned_pdf(file_path: str) -> bool:
    """
    Detect if PDF is scanned (image-based, no selectable text).

    Returns True if text extraction ratio is very low.
    Threshold: average < 20 characters per page indicates scanned PDF.
    For CJK documents, characters carry more information per glyph,
    so this threshold is intentionally low.
    """
    if not HAS_PYMUPDF:
        return False

    doc = None
    try:
        doc = fitz.open(file_path)
        total_chars = 0
        total_pages = len(doc)
        if total_pages == 0:
            return False

        # Sample first few pages for speed on large documents
        sample_pages = min(total_pages, 10)
        for i in range(sample_pages):
            text = doc[i].get_text()
            total_chars += len(text.strip())

        avg_chars_per_page = total_chars / sample_pages
        return avg_chars_per_page < 20
    except Exception:
        return False
    finally:
        if doc is not None:
            doc.close()


def is_complex_pdf(file_path: str) -> bool:
    """
    Detect if PDF has complex layout that likely benefits from OCR/layout analysis.

    Uses conservative thresholds to avoid routing ordinary lecture notes
    (long but text-heavy) to the slow heavy path.

    Returns True if:
    - PDF has > 200 pages AND many image-heavy pages (visual textbooks / atlases)
    - Multiple sample pages are image-dominant with very little text
    """
    if not HAS_PYMUPDF:
        return False

    doc = None
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        if total_pages == 0:
            return False

        sample_pages = min(total_pages, 10)
        total_chars = 0
        image_heavy_pages = 0

        for i in range(sample_pages):
            page = doc[i]
            text = page.get_text().strip()
            total_chars += len(text)

            # Count images (exclude tiny stamps / watermarks)
            image_count = len(page.get_images())
            if image_count > 5:
                image_heavy_pages += 1

        avg_chars_per_page = total_chars / sample_pages

        # Only route to heavy if it is genuinely image-dominant
        if total_pages > 200 and image_heavy_pages >= 5:
            return True

        if image_heavy_pages >= 3 and avg_chars_per_page < 50:
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
