"""Runtime configuration loading for Papyrus."""

from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "format": "markdown",
    "cache": True,
    "use_heavy": False,
    "use_fast": False,
    "batch_executor": "threads",
    "workers": None,
}


def config_path() -> Path:
    return Path.home() / ".papyrus" / "config.toml"


def load_config() -> dict[str, Any]:
    """Load ~/.papyrus/config.toml if present.

    Supported keys under [defaults]:
    - format = "markdown" | "json"
    - cache = true | false
    - use_heavy = true | false
    - use_fast = true | false
    - batch_executor = "threads" | "processes"
    - workers = 4
    """
    path = config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)

    try:
        data = _load_toml(path)
    except Exception:
        return dict(DEFAULT_CONFIG)

    defaults = data.get("defaults", data) if isinstance(data, dict) else {}
    config = dict(DEFAULT_CONFIG)
    if defaults.get("format") in {"markdown", "json"}:
        config["format"] = defaults["format"]
    if isinstance(defaults.get("cache"), bool):
        config["cache"] = defaults["cache"]
    if isinstance(defaults.get("use_heavy"), bool):
        config["use_heavy"] = defaults["use_heavy"]
    if isinstance(defaults.get("use_fast"), bool):
        config["use_fast"] = defaults["use_fast"]
    if config["use_heavy"] and config["use_fast"]:
        config["use_heavy"] = False
        config["use_fast"] = False
    if defaults.get("batch_executor") in {"threads", "processes"}:
        config["batch_executor"] = defaults["batch_executor"]
    if isinstance(defaults.get("workers"), int) and defaults["workers"] > 0:
        config["workers"] = defaults["workers"]
    return config


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib

        with path.open("rb") as fh:
            return tomllib.load(fh)
    except ModuleNotFoundError:
        return _load_simple_toml(path)


def _load_simple_toml(path: Path) -> dict[str, Any]:
    """Tiny TOML subset parser for Python 3.8/3.9 without tomllib."""
    data: dict[str, Any] = {}
    current: dict[str, Any] = data
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = data.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        current[key] = _parse_value(value)
    return data


def _parse_value(value: str) -> Any:
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value
