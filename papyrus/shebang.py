"""Repair scripts generated inside Papyrus virtual environments."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional, Union


def repair_shebangs(
    venv_path: Union[str, Path],
    python_path: Optional[Union[str, Path]] = None,
) -> dict:
    """Rewrite stale shebangs in venv/bin scripts to the current venv Python.

    Moving a virtual environment directory leaves console scripts pointing at the
    old absolute Python path. This fixes text scripts whose first line starts
    with "#!" and contains "python".
    """
    venv = Path(venv_path).expanduser().resolve()
    bin_dir = venv / ("Scripts" if os.name == "nt" else "bin")
    if python_path is None:
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
    else:
        python = Path(python_path).expanduser().resolve()

    result = {
        "venv": str(venv),
        "python": str(python),
        "checked": 0,
        "repaired": 0,
        "skipped": 0,
    }

    if not bin_dir.exists():
        raise FileNotFoundError(f"Virtual environment bin directory not found: {bin_dir}")
    if not python.exists():
        raise FileNotFoundError(f"Virtual environment Python not found: {python}")

    shebang = f"#!{python}\n".encode("utf-8")
    for script in _iter_script_files(bin_dir):
        result["checked"] += 1
        try:
            data = script.read_bytes()
        except OSError:
            result["skipped"] += 1
            continue
        if not data.startswith(b"#!"):
            result["skipped"] += 1
            continue
        first_line, sep, rest = data.partition(b"\n")
        if b"python" not in first_line.lower():
            result["skipped"] += 1
            continue
        if first_line + sep == shebang:
            continue
        script.write_bytes(shebang + rest)
        result["repaired"] += 1

    return result


def _iter_script_files(bin_dir: Path) -> Iterable[Path]:
    for path in sorted(bin_dir.iterdir()):
        if path.is_file() and not path.name.startswith("python"):
            yield path
