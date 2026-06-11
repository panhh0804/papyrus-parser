"""Error classification and document validation."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

from .detector import detect_file_type


class PapyrusError(Exception):
    """Base class for Papyrus user-facing errors."""

    category = "parse_error"
    suggestion = "Check that the file opens normally, then retry."


class UnsupportedFormatError(PapyrusError, ValueError):
    category = "unsupported_format"
    suggestion = "Use PDF, PPTX, DOCX, XLSX, HTML, Markdown, or plain text."


class CorruptFileError(PapyrusError, RuntimeError):
    category = "corrupt_file"
    suggestion = "Re-download or re-copy the file, then retry with the complete original file."


class TemporaryFileError(PapyrusError, RuntimeError):
    category = "temporary_file"
    suggestion = "检测到 Word/Office 临时锁定文件，请使用原始 .docx/.pptx/.xlsx 文件。"


class EncryptedFileError(PapyrusError, RuntimeError):
    category = "encrypted_file"
    suggestion = "Unlock or decrypt the file first, then run Papyrus again."


class EmptyOutputError(PapyrusError, RuntimeError):
    category = "empty_output"
    suggestion = "If this is a scanned PDF, retry with --use-heavy. Otherwise verify the file is complete."


class MissingDependencyError(PapyrusError, ImportError):
    category = "missing_dependency"
    suggestion = "Install the missing dependency or rerun the Papyrus setup script."


class OcrTimeoutError(PapyrusError, TimeoutError):
    category = "ocr_timeout"
    suggestion = "Retry with --use-fast, split the document, or run OCR on a smaller file."


def validate_document_file(file_path: str) -> None:
    """Fail early for common invalid or incomplete document files."""
    path = Path(file_path)
    name = path.name
    lower_name = name.lower()

    if name.startswith("~$") or name.startswith(".~") or lower_name.endswith(".tmp"):
        raise TemporaryFileError(
            f"{path}: detected an Office temporary/lock file, not the original document."
        )

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise CorruptFileError(f"{path}: cannot read file metadata: {exc}") from exc

    if size == 0:
        raise CorruptFileError(f"{path}: file is empty (0 bytes).")

    file_type = detect_file_type(str(path))
    if file_type in {"docx", "pptx", "excel"}:
        _validate_ooxml(path, file_type)
    elif file_type == "pdf":
        _validate_pdf(path)


def ensure_non_empty_output(result: dict, file_path: str) -> None:
    """Raise a classified error when a parser silently returns no content."""
    content = result.get("content", "")
    if isinstance(content, str) and content.strip():
        return
    file_type = detect_file_type(file_path)
    if file_type == "pdf":
        raise EmptyOutputError(
            f"{file_path}: parser returned empty output. This may be a scanned, encrypted, or corrupt PDF."
        )
    raise EmptyOutputError(
        f"{file_path}: parser returned empty output. The file may be temporary, corrupt, or unsupported by the selected parser."
    )


def friendly_error_message(exc: Exception, file_path: Optional[str] = None) -> str:
    """Return a concise user-facing message with a concrete next step."""
    prefix = f"{file_path}: " if file_path else ""
    if isinstance(exc, PapyrusError):
        return f"{prefix}{exc}\nSuggestion: {exc.suggestion}"
    if isinstance(exc, FileNotFoundError):
        return f"{prefix}{exc}\nSuggestion: Check the path and file name."
    if isinstance(exc, PermissionError):
        return f"{prefix}{exc}\nSuggestion: Fix file permissions or close the app locking this file."
    if isinstance(exc, ImportError):
        return f"{prefix}{exc}\nSuggestion: Install missing dependencies, or run setup-unix.sh again."

    text = str(exc)
    lowered = text.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return f"{prefix}{text}\nSuggestion: OCR timed out. Try --use-fast or split the document."
    if "password" in lowered or "encrypted" in lowered:
        return f"{prefix}{text}\nSuggestion: Unlock/decrypt the file before parsing."
    if "numpy.dtype size changed" in lowered:
        return (
            f"{prefix}{text}\n"
            "Suggestion: Reinstall with numpy<2.0: pip install 'numpy<2.0' --force-reinstall"
        )
    return f"{prefix}{text}"


def _validate_ooxml(path: Path, file_type: str) -> None:
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            if "[Content_Types].xml" not in names:
                raise CorruptFileError(f"{path}: Office document is missing [Content_Types].xml.")
            required_prefixes = {
                "docx": "word/",
                "pptx": "ppt/",
                "excel": "xl/",
            }
            prefix = required_prefixes[file_type]
            if not any(name.startswith(prefix) for name in names):
                raise CorruptFileError(f"{path}: Office document is missing expected {prefix} content.")
            bad_file = zf.testzip()
            if bad_file:
                raise CorruptFileError(f"{path}: Office archive contains a corrupt member: {bad_file}.")
    except zipfile.BadZipFile as exc:
        raise CorruptFileError(f"{path}: Office document is not a valid zip archive.") from exc


def _validate_pdf(path: Path) -> None:
    try:
        import fitz
    except ImportError:
        return

    doc = None
    try:
        doc = fitz.open(str(path))
        if getattr(doc, "is_encrypted", False) or getattr(doc, "needs_pass", False):
            raise EncryptedFileError(f"{path}: PDF is encrypted or password-protected.")
        if len(doc) == 0:
            raise CorruptFileError(f"{path}: PDF has zero pages.")
    except PapyrusError:
        raise
    except Exception as exc:
        raise CorruptFileError(f"{path}: PDF cannot be opened: {exc}") from exc
    finally:
        if doc is not None:
            doc.close()
