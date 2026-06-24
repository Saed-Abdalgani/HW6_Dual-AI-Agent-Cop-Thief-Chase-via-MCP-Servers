"""Config file loading and secret helpers.

Factored out of :mod:`.config` to keep each module under ~150 LOC.

Traces: FR-C1, FR-C3, T-P0-08, T-P0-11.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

_dotenv_loaded = False


def ensure_dotenv_loaded() -> None:
    """Load ``.env`` from the project root once per process."""
    global _dotenv_loaded
    if not _dotenv_loaded:
        load_dotenv()
        _dotenv_loaded = True


def load_yaml(path: str | Path) -> dict:
    """Load and parse a YAML config file.

    Args:
        path: Absolute or relative path to the YAML file.

    Returns:
        Parsed dictionary (empty dict if file is blank).

    Raises:
        FileNotFoundError: If *path* does not exist.

    """
    path = Path(path)
    if not path.exists():
        msg = f"Config file not found: {path}"
        raise FileNotFoundError(msg)
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def apply_env_overrides(data: dict) -> dict:
    """Apply non-secret env overrides (e.g. public MCP URLs) to raw config data."""
    mcp = dict(data.get("mcp") or {})
    if mode := os.environ.get("MCP_MODE"):
        mcp["mode"] = mode
    if auto_launch := os.environ.get("MCP_AUTO_LAUNCH"):
        mcp["auto_launch"] = auto_launch.lower() in {"1", "true", "yes", "on"}
    if cop_url := os.environ.get("MCP_COP_URL"):
        mcp["cop_url"] = cop_url
    if thief_url := os.environ.get("MCP_THIEF_URL"):
        mcp["thief_url"] = thief_url
    if mcp:
        data["mcp"] = mcp
    return data


def load_secret(env_var: str, *, required: bool = True) -> str | None:
    """Return the value of *env_var*; raise if missing and *required*.

    Secrets are **never** logged.

    Args:
        env_var: Name of the environment variable.
        required: When ``True``, raise :class:`OSError` if the var is unset.

    Returns:
        The env-var value, or ``None`` if not set and not required.

    Raises:
        OSError: When *required* is ``True`` and the var is absent or empty.

    """
    ensure_dotenv_loaded()
    value = os.environ.get(env_var)
    if required and not value:
        msg = (
            f"Required secret '{env_var}' is not set. "
            f"See .env-example for the full list of required env vars."
        )
        raise OSError(msg)
    return value
