"""Auth types: TokenRecord dataclass.

Factored out of :mod:`.auth` to keep each module under ~150 LOC.

Traces: NFR-1, NFR-2, T-P0-22.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TokenRecord:
    """Metadata stored for each issued token (never stores the raw token).

    Attributes:
        token_id: Unique opaque identifier for the token slot.
        token_hash: HMAC-SHA256 hex digest of the raw token.
        agent: Logical name of the owning agent (e.g. ``"cop"``).
        issued_at: UTC datetime when the token was issued.
        revoked: ``True`` once the token has been revoked.

    """

    token_id: str
    token_hash: str
    agent: str
    issued_at: datetime
    revoked: bool = False
