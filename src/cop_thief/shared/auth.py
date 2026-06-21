
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
import threading
from datetime import UTC, datetime
from cop_thief.shared._auth_types import TokenRecord
__all__ = ["TokenRecord", "TokenStore", "default_store"]


class TokenStore:
    """Thread-safe token registry: issue, verify, and revoke bearer tokens.

    Usage::

        store = TokenStore()
        raw_token = store.issue("cop")   # give this to the cop MCP client
        store.verify(raw_token)           # → True
        store.revoke(raw_token)
        store.verify(raw_token)           # → False

    The raw token is **never** stored — only its HMAC-SHA256 hash is kept.
    """

    def __init__(self) -> None:
        """Initialize the token store with a fresh in-process HMAC secret."""
        self._secret: bytes = os.urandom(32)
        self._records: dict[str, TokenRecord] = {}
        self._hash_index: dict[str, str] = {}
        self._lock = threading.Lock()

    def issue(self, agent: str) -> str:
        """Generate and register a new bearer token for *agent*.

        Args:
            agent: Logical name of the agent (e.g. ``"cop"`` or ``"thief"``).

        Returns:
            The raw token string. **Return this to the caller exactly once.**

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
    def register_token(self, agent: str, raw_token: str) -> None:
        """Register a pre-determined raw token for *agent*.

        Args:
            agent: Logical name of the agent (e.g. ``"cop"`` or ``"thief"``).
            raw_token: The raw token string to register.

        """
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

    def get_agent(self, raw_token: str) -> str | None:
        """Return the agent name associated with the raw token if valid.

        Args:
            raw_token: The bearer token to inspect.

        Returns:
            The associated agent name if the token is valid; ``None`` otherwise.

        """
        token_hash = self._hash(raw_token)
        with self._lock:
            token_id = self._hash_index.get(token_hash)
            if token_id is None:
                return None
            record = self._records.get(token_id)
            if record is None or record.revoked:
                return None
            return record.agent

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
            ``True`` if found and revoked; ``False`` if unknown or already revoked.

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

    def _hash(self, raw_token: str) -> str:
        """Return the HMAC-SHA256 hex digest of *raw_token*."""
        return hmac.new(self._secret, raw_token.encode(), hashlib.sha256).hexdigest()
default_store: TokenStore = TokenStore()