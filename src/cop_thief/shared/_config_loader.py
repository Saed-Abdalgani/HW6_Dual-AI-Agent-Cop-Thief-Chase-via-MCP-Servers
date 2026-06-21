"""Config file loading and secret helpers.

Factored out of :mod:`.config` to keep each module under ~150 LOC.

Traces: FR-C1, FR-C3, T-P0-08, T-P0-11.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


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
    value = os.environ.get(env_var)
    if required and not value:
        msg = (
            f"Required secret '{env_var}' is not set. "
            f"See .env-example for the full list of required env vars."
        )
        raise OSError(msg)
    return value
