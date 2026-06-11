"""Image extraction helpers for document assets."""

from __future__ import annotations

import os
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable

from .detector import detect_file_type

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
    ".emf",
    ".wmf",
}


def default_image_dir(file_path: str, output_path: str | None = None) -> Path:
    """Return the default image output directory for a parse request."""
    if output_path:
        output = Path(output_path).expanduser()
        return output.parent / f"{output.stem}_images"

    source = Path(file_path)
    stem = source.stem or "stdin"
    return Path.cwd() / f"{_safe_stem(stem)}_images"


def extract_images(
    file_path: str,
    output_dir: str | Path,
    reference_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Extract images from supported document types.

    Supported extraction strategies:
    - PDF: PyMuPDF image xref extraction
    - PPTX: raw media files under ppt/media/
    - DOCX: raw media files under word/media/
    """
    file_type = detect_file_type(file_path)
    out_dir = Path(output_dir).expanduser().resolve()
    ref_dir = Path(reference_dir or Path.cwd()).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if file_type == "pdf":
        images = _extract_pdf_images(file_path, out_dir)
    elif file_type == "pptx":
        images = _extract_zip_media(file_path, out_dir, "ppt/media")
    elif file_type == "docx":
        images = _extract_zip_media(file_path, out_dir, "word/media")
    else:
        images = []

    for image in images:
        image_path = Path(image["path"])
        image["relative_path"] = _posix_relpath(image_path, ref_dir)
    return images


def append_image_section(content: str, images: list[dict[str, Any]]) -> str:
    """Append a stable Markdown image index to parsed content."""
    if not images:
        return content

    lines = [content.rstrip(), "", "---", "", "# Extracted Images", ""]
    for image in images:
        label = _image_label(image)
        lines.append(f"![{label}]({image['relative_path']})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _extract_pdf_images(file_path: str, output_dir: Path) -> list[dict[str, Any]]:
    if not HAS_FITZ:
        raise ImportError("PyMuPDF is required for PDF image extraction")

    doc = None
    images: list[dict[str, Any]] = []
    try:
        doc = fitz.open(file_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                xref = image_info[0]
                extracted = doc.extract_image(xref)
                image_bytes = extracted.get("image")
                if not image_bytes:
                    continue
                ext = extracted.get("ext") or "png"
                filename = f"page-{page_index + 1:04d}-image-{image_index:03d}.{ext}"
                path = _unique_path(output_dir / filename)
                path.write_bytes(image_bytes)
                images.append(
                    {
                        "index": len(images) + 1,
                        "type": "pdf-image",
                        "page": page_index + 1,
                        "source": f"page:{page_index + 1}:xref:{xref}",
                        "filename": path.name,
                        "path": str(path),
                        "width": extracted.get("width"),
                        "height": extracted.get("height"),
                        "extension": ext,
                    }
                )
    finally:
        if doc is not None:
            doc.close()
    return images


def _extract_zip_media(file_path: str, output_dir: Path, media_prefix: str) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    with zipfile.ZipFile(file_path) as archive:
        for member in _iter_media_members(archive, media_prefix):
            source_name = Path(member).name
            output_name = f"image-{len(images) + 1:04d}-{_safe_filename(source_name)}"
            path = _unique_path(output_dir / output_name)
            path.write_bytes(archive.read(member))
            images.append(
                {
                    "index": len(images) + 1,
                    "type": "embedded-media",
                    "source": member,
                    "filename": path.name,
                    "path": str(path),
                    "extension": path.suffix.lower().lstrip(".") or None,
                }
            )
    return images


def _iter_media_members(archive: zipfile.ZipFile, media_prefix: str) -> Iterable[str]:
    prefix = media_prefix.rstrip("/") + "/"
    members = []
    for member in archive.namelist():
        if not member.startswith(prefix):
            continue
        name = Path(member).name
        if not name:
            continue
        if Path(name).suffix.lower() in IMAGE_EXTENSIONS:
            members.append(member)
    return sorted(members)


def _image_label(image: dict[str, Any]) -> str:
    page = image.get("page")
    if page:
        return f"Image {image['index']} from page {page}"
    source = image.get("source")
    if source:
        return f"Image {image['index']} from {source}"
    return f"Image {image['index']}"


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "document"


def _safe_filename(value: str) -> str:
    name = Path(value).name
    stem = _safe_stem(Path(name).stem)
    suffix = Path(name).suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        suffix = ".bin"
    return stem + suffix


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _posix_relpath(path: Path, reference_dir: Path) -> str:
    return os.path.relpath(path, start=reference_dir).replace(os.sep, "/")
