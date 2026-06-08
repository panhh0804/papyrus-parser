"""Heavy path: advanced parsing using marker for complex PDFs."""

import json
from pathlib import Path
from typing import Dict, Any
import subprocess
import sys

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    HAS_MARKER = True
except ImportError:
    HAS_MARKER = False


def parse_with_marker(
    file_path: str,
    output_format: str = "markdown",
) -> Dict[str, Any]:
    """
    Parse PDF using marker (heavy-weight, good for scanned/complex PDFs).

    Args:
        file_path: Path to the PDF file
        output_format: "markdown" or "json"

    Returns:
        Dict with 'content' and 'format' keys
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Heavy path (marker) only supports PDFs, got: {path.suffix}")

    if not HAS_MARKER:
        raise ImportError(
            "marker-pdf not installed. To use heavy path, run:\n"
            "  pip install marker-pdf\n"
            "Or for additional features:\n"
            "  pip install 'papyrus[heavy]'"
        )

    try:
        # Initialize models (this may take a while on first run)
        model_dict = create_model_dict()

        # Convert PDF to markdown
        converter = PdfConverter(
            artifact_dict=model_dict,
        )
        rendered = converter(file_path)
        content = rendered.markdown

        if output_format == "json":
            return {
                "content": content,
                "format": "json",
                "metadata": {
                    "file": path.name,
                    "size_bytes": path.stat().st_size,
                    "parser": "marker",
                    "pages": rendered.num_pages if hasattr(rendered, 'num_pages') else None,
                },
            }

        return {
            "content": content,
            "format": "markdown",
        }

    except Exception as e:
        raise RuntimeError(f"Marker parsing failed: {str(e)}") from e


def parse_with_marker_cli(
    file_path: str,
    output_format: str = "markdown",
    use_gpu: bool = False,
) -> Dict[str, Any]:
    """
    Parse PDF using marker CLI (subprocess fallback).

    Useful if marker SDK is not available but CLI is installed.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        cmd = ["marker_pdf", str(file_path), "-o", "json" if output_format == "json" else "md"]
        if use_gpu:
            cmd.append("--gpu")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5-minute timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"marker_pdf failed: {result.stderr}")

        content = result.stdout

        return {
            "content": content,
            "format": output_format,
            "metadata": {
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "parser": "marker-cli",
            },
        }

    except FileNotFoundError:
        raise ImportError(
            "marker_pdf CLI not found. Install marker-pdf:\n"
            "  pip install 'marker-pdf[cli]'\n"
            "Or: pip install 'doc-parse[heavy]'"
        )
    except Exception as e:
        raise RuntimeError(f"Marker CLI parsing failed: {str(e)}") from e
