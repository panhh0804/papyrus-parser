"""Document metadata extraction helpers."""

from __future__ import annotations

import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .detector import detect_file_type

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


def _iso_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def extract_metadata(file_path: str) -> dict[str, Any]:
    """Extract stable file and document metadata without doing full parsing."""
    path = Path(file_path)
    stat = path.stat()
    metadata: dict[str, Any] = {
        "file": path.name,
        "path": str(path.resolve()),
        "suffix": path.suffix.lower(),
        "type": detect_file_type(str(path)),
        "mime_type": mimetypes.guess_type(str(path))[0],
        "size_bytes": stat.st_size,
        "modified_at": _iso_timestamp(stat.st_mtime),
        "created_at": _iso_timestamp(stat.st_ctime),
    }

    if metadata["type"] == "pdf":
        metadata.update(_pdf_metadata(str(path)))

    return metadata


def _pdf_metadata(file_path: str) -> dict[str, Any]:
    if not HAS_FITZ:
        return {}

    doc = None
    try:
        doc = fitz.open(file_path)
        raw = doc.metadata or {}
        return {
            "pages": len(doc),
            "encrypted": bool(getattr(doc, "is_encrypted", False)),
            "title": raw.get("title") or None,
            "author": raw.get("author") or None,
            "subject": raw.get("subject") or None,
            "keywords": raw.get("keywords") or None,
            "creator": raw.get("creator") or None,
            "producer": raw.get("producer") or None,
            "creation_date": raw.get("creationDate") or None,
            "modification_date": raw.get("modDate") or None,
        }
    except Exception:
        return {}
    finally:
        if doc is not None:
            doc.close()


def merge_metadata(result: dict, file_path: str) -> dict:
    """Merge parser metadata with file/document metadata."""
    merged = extract_metadata(file_path)
    merged.update(result.get("metadata") or {})
    result["metadata"] = merged
    return result
