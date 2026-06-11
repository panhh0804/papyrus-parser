"""Content-addressed cache for parsed documents."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from . import __version__


def get_cache_dir() -> Path:
    """Return the Papyrus cache directory."""
    override = os.environ.get("PAPYRUS_CACHE_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / "papyrus"


def file_digest(file_path: str) -> str:
    """Compute a SHA256 digest for a file without loading it all at once."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(
    file_path: str,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
) -> str:
    """Build a cache key from file content and parse options."""
    payload = {
        "version": __version__,
        "digest": file_digest(file_path),
        "format": output_format,
        "force_heavy": force_heavy,
        "force_fast": force_fast,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_cached_result(
    file_path: str,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
) -> Optional[dict]:
    """Load a cached parse result, returning None on cache miss/corruption."""
    key = cache_key(file_path, output_format, force_heavy, force_fast)
    cache_file = get_cache_dir() / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        result = json.loads(cache_file.read_text(encoding="utf-8"))
        result = copy.deepcopy(result)
        metadata = result.setdefault("metadata", {})
        metadata["cache_hit"] = True
        metadata["cache_key"] = key
        return result
    except Exception:
        return None


def store_cached_result(
    file_path: str,
    output_format: str,
    force_heavy: bool,
    force_fast: bool,
    result: dict,
) -> None:
    """Store a parse result in the cache."""
    key = cache_key(file_path, output_format, force_heavy, force_fast)
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{key}.json"

    payload = copy.deepcopy(result)
    metadata = payload.setdefault("metadata", {})
    metadata["cache_hit"] = False
    metadata["cache_key"] = key
    tmp_file = cache_file.with_name(f"{cache_file.name}.{uuid.uuid4().hex}.tmp")
    tmp_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp_file.replace(cache_file)


def cache_info() -> dict:
    """Return cache location, file count, and byte size."""
    cache_dir = get_cache_dir()
    files = list(cache_dir.glob("*.json")) if cache_dir.exists() else []
    size_bytes = sum(p.stat().st_size for p in files if p.is_file())
    return {
        "cache_dir": str(cache_dir),
        "entries": len(files),
        "size_bytes": size_bytes,
    }


def clear_cache() -> dict:
    """Delete all Papyrus cache entries."""
    info = cache_info()
    cache_dir = get_cache_dir()
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    return info
