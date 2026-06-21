"""TokenStore lifecycle tests — T-P0-25 (part 1/2).

Covers:
- issue() returns a non-empty unique string.
- verify() is True for a freshly issued token.
- verify() is False for an unknown token.
- revoke() makes verify() return False.
- revoke() returns False if already revoked or unknown.
- active_count() increments on issue and decrements on revoke.
- Multiple tokens are independent.
- Issued tokens are all unique.
"""

from __future__ import annotations

from cop_thief.shared.auth import TokenStore


class TestTokenStore:
    def test_issue_returns_string(self) -> None:
        store = TokenStore()
        token = store.issue("cop")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_issued_token(self) -> None:
        store = TokenStore()
        token = store.issue("thief")
        assert store.verify(token) is True

    def test_verify_unknown_token(self) -> None:
        store = TokenStore()
        assert store.verify("not-a-real-token") is False

    def test_revoke_invalidates_token(self) -> None:
        store = TokenStore()
        token = store.issue("cop")
        assert store.revoke(token) is True
        assert store.verify(token) is False

    def test_revoke_already_revoked_returns_false(self) -> None:
        store = TokenStore()
        token = store.issue("cop")
        store.revoke(token)
        assert store.revoke(token) is False

    def test_revoke_unknown_token_returns_false(self) -> None:
        store = TokenStore()
        assert store.revoke("ghost-token") is False

    def test_active_count_increments_on_issue(self) -> None:
        store = TokenStore()
        assert store.active_count() == 0
        store.issue("cop")
        assert store.active_count() == 1
        store.issue("thief")
        assert store.active_count() == 2

    def test_active_count_decrements_on_revoke(self) -> None:
        store = TokenStore()
        t1 = store.issue("cop")
        t2 = store.issue("thief")
        store.revoke(t1)
        assert store.active_count() == 1
        store.revoke(t2)
        assert store.active_count() == 0

    def test_multiple_tokens_are_independent(self) -> None:
        store = TokenStore()
        t1 = store.issue("cop")
        t2 = store.issue("thief")
        store.revoke(t1)
        assert store.verify(t1) is False
        assert store.verify(t2) is True

    def test_issued_tokens_are_unique(self) -> None:
        store = TokenStore()
        tokens = {store.issue("cop") for _ in range(10)}
        assert len(tokens) == 10
