"""Verbose progress probes for large documents."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Optional

import click


def show_document_progress(file_path: str, file_type: Optional[str] = None) -> None:
    """Show lightweight page/slide progress in verbose CLI runs.

    Third-party parsers do not expose reliable callbacks, so this probe gives
    users immediate feedback that a large file is being inspected before the
    actual parse begins.
    """
    path = Path(file_path)
    file_type = file_type or path.suffix.lower().lstrip(".")
    if file_type == "pdf":
        _show_pdf_progress(path)
    elif file_type == "pptx":
        _show_pptx_progress(path)


def _show_pdf_progress(path: Path) -> None:
    try:
        import fitz
    except ImportError:
        return

    doc = None
    try:
        doc = fitz.open(str(path))
        total = len(doc)
        if total <= 1:
            return
        click.echo(f"📖 PDF pages: {total}", err=True)
        with click.progressbar(
            range(total),
            label="Inspecting PDF pages",
            file=sys.stderr,
            show_eta=False,
        ) as pages:
            for index in pages:
                doc.load_page(index)
    except Exception:
        return
    finally:
        if doc is not None:
            doc.close()


def _show_pptx_progress(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as zf:
            slides = sorted(
                name
                for name in zf.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            if len(slides) <= 1:
                return
            click.echo(f"📊 PPTX slides: {len(slides)}", err=True)
            with click.progressbar(
                slides,
                label="Inspecting PPTX slides",
                file=sys.stderr,
                show_eta=False,
            ) as slide_names:
                for name in slide_names:
                    zf.getinfo(name)
    except Exception:
        return
