"""Parsing implementations for different strategies."""

from .fast_path import parse_with_fast_path
from .heavy_path import parse_with_marker

__all__ = ["parse_with_fast_path", "parse_with_marker"]
