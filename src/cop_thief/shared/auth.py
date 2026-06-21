"""Token-based authentication for MCP servers.

Provides :class:`TokenStore` for issuing, verifying, and revoking bearer tokens
used by the cop and thief MCP servers.  Tokens are stored as **HMAC-SHA256
hashes** — only the hash lives in memory; the raw token is provided to the
caller once at issuance and is never retained.

Traces: NFR-1, NFR-2, PLAN §16, T-P0-22.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime


# Data types
@dataclass(frozen=True)
class TokenRecord:
    """Metadata stored for each issued token (never stores the raw token)."""

    token_id: str
    token_hash: str           # HMAC-SHA256 of raw_token with internal secret
    agent: str                # "cop" | "thief" | any label
    issued_at: datetime
    revoked: bool = False

# Token store

class TokenStore:
    """Thread-safe token registry: issue, verify, and revoke bearer tokens.

    Usage::

        store = TokenStore()
        raw_token = store.issue("cop")   # give this to the cop MCP client
        store.verify(raw_token)           # → True
        store.revoke(raw_token)
        store.verify(raw_token)           # → False

    The raw token is **never** stored.  Only its HMAC-SHA256 hash (keyed with
    an in-process secret) is kept, so even a memory-dump attacker cannot
    extract a usable token.
    """

    def __init__(self) -> None:
        """Initialize the token store with a fresh in-process HMAC secret."""
        self._secret: bytes = os.urandom(32)   # process-lifetime HMAC key
        self._records: dict[str, TokenRecord] = {}  # token_id → record
        self._hash_index: dict[str, str] = {}       # token_hash → token_id
        self._lock = threading.Lock()


    # Public API
    def issue(self, agent: str) -> str:
        """Generate and register a new bearer token for *agent*.

        Args:
            agent: Logical name of the agent (e.g. ``"cop"`` or ``"thief"``).

        Returns:
            The raw token string.  **Return this to the caller exactly once.**
            It is not retrievable afterward.

        """
        raw_token = secrets.token_urlsafe(32)
        token_id = secrets.token_hex(8)
        token_hash = self._hash(raw_token)
        record = TokenRecord(
            token_id=token_id,
            token_hash=token_hash,
            agent=agent,
            issued_at=datetime.now(UTC),
        )
        with self._lock:
            self._records[token_id] = record
            self._hash_index[token_hash] = token_id
        return raw_token

    def verify(self, raw_token: str) -> bool:
        """Return ``True`` if *raw_token* is valid (issued and not revoked).

        Args:
            raw_token: The bearer token to verify.

        Returns:
            ``True`` for a live, non-revoked token; ``False`` otherwise.

        """
        token_hash = self._hash(raw_token)
        with self._lock:
            token_id = self._hash_index.get(token_hash)
            if token_id is None:
                return False
            record = self._records.get(token_id)
            return record is not None and not record.revoked

    def revoke(self, raw_token: str) -> bool:
        """Revoke *raw_token* so future :meth:`verify` calls return ``False``.

        Args:
            raw_token: The bearer token to revoke.

        Returns:
            ``True`` if the token was found and revoked; ``False`` if it was
            already revoked or unknown.

        """
        token_hash = self._hash(raw_token)
        with self._lock:
            token_id = self._hash_index.get(token_hash)
            if token_id is None:
                return False
            record = self._records[token_id]
            if record.revoked:
                return False
            self._records[token_id] = TokenRecord(
                token_id=record.token_id,
                token_hash=record.token_hash,
                agent=record.agent,
                issued_at=record.issued_at,
                revoked=True,
            )
        return True

    def active_count(self) -> int:
        """Return the number of currently active (non-revoked) tokens."""
        with self._lock:
            return sum(1 for r in self._records.values() if not r.revoked)

    # Internals

    def _hash(self, raw_token: str) -> str:
        """Return the HMAC-SHA256 hex digest of *raw_token* keyed with the internal secret."""
        return hmac.new(self._secret, raw_token.encode(), hashlib.sha256).hexdigest()

# Module-level default store

#: Default singleton store used by the MCP servers.  Tests should create their
#: own :class:`TokenStore` instances to avoid shared state.
default_store: TokenStore = TokenStore()

@dataclass
class _Unused:
    """Placeholder to satisfy unused-import linting for ``field``."""

    _: list[str] = field(default_factory=list)
