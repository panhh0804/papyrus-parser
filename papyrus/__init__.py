"""Papyrus: Universal document parser for Claude Code, Codex, Kimi."""

__version__ = "0.1.0"
__author__ = "Pan Haohao"

from .detector import detect_file_type, is_scanned_document
from .router import route_file
from .parsers.fast_path import parse_with_fast_path
from .parsers.heavy_path import parse_with_marker

__all__ = [
    "detect_file_type",
    "is_scanned_document",
    "route_file",
    "parse_with_fast_path",
    "parse_with_marker",
]
