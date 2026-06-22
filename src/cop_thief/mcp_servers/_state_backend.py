"""Shared game-state backends for local and multi-container MCP runs.

Traces: FR-MCP5, T-P7-02, T-P7-03.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol

from cop_thief.shared._config_loader import load_secret


class StateBackend(Protocol):
    """Read/write JSON game state."""

    def read(self) -> dict | None:
        """Return stored state or ``None`` when unset."""

    def write(self, state: dict) -> None:
        """Persist *state*."""


class FileStateBackend:
    """Persist state to a local JSON file with cross-process locking."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> dict | None:
        return self._with_lock(self._read_unlocked)

    def write(self, state: dict) -> None:
        self._with_lock(lambda: self._write_unlocked(state))

    def _read_unlocked(self) -> dict | None:
        if not self._path.exists():
            return None
        try:
            with self._path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError:
            self._path.unlink(missing_ok=True)
            return None

    def _write_unlocked(self, state: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)

    def _with_lock(self, fn: object) -> dict | None:
        lock = self._path.with_suffix(f"{self._path.suffix}.lock")
        fd: int | None = None
        for _ in range(100):
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                time.sleep(0.02)
        else:
            msg = f"Could not acquire state lock: {lock}"
            raise TimeoutError(msg)
        try:
            return fn()  # type: ignore[call-arg, no-any-return]
        finally:
            if fd is not None:
                os.close(fd)
            lock.unlink(missing_ok=True)


class HttpStateBackend:
    """Persist state via the shared HTTP state service."""

    def __init__(self, base_url: str, token: str) -> None:
        self._url = f"{base_url.rstrip('/')}/"
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def read(self) -> dict | None:
        req = urllib.request.Request(self._url, headers=self._headers(), method="GET")  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:  # noqa: PLR2004
                return None
            raise
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) and data else None

    def write(self, state: dict) -> None:
        body = json.dumps(state).encode()
        req = urllib.request.Request(  # noqa: S310
            self._url,
            data=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            resp.read()


_backend: StateBackend | None = None


def get_state_backend(path: Path) -> StateBackend:
    """Return the configured backend, caching the first resolved instance."""
    global _backend
    if _backend is not None:
        return _backend
    override = os.environ.get("MCP_STATE_PATH")
    if override:
        _backend = FileStateBackend(Path(override))
        return _backend
    state_url = os.environ.get("MCP_STATE_URL", "").strip()
    if state_url:
        token = load_secret("MCP_STATE_TOKEN")
        _backend = HttpStateBackend(state_url, token or "")
    else:
        _backend = FileStateBackend(path)
    return _backend


def reset_state_backend() -> None:
    """Clear the cached backend (used in tests)."""
    global _backend
    _backend = None
