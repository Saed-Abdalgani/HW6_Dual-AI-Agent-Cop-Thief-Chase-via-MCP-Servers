"""Unit tests for MCP authorization and token registration."""

from __future__ import annotations

import pytest

from cop_thief.mcp_servers.tools import authorize
from cop_thief.shared.auth import TokenStore, default_store


class TestMcpAuth:
    def test_register_and_get_agent(self) -> None:
        store = TokenStore()
        raw_tok = "my-custom-cop-token"
        store.register_token("cop", raw_tok)
        assert store.get_agent(raw_tok) == "cop"
        assert store.verify(raw_tok) is True

    def test_get_agent_unknown_or_revoked(self) -> None:
        store = TokenStore()
        raw_tok = "my-custom-thief-token"
        assert store.get_agent(raw_tok) is None

        store.register_token("thief", raw_tok)
        assert store.get_agent(raw_tok) == "thief"

        store.revoke(raw_tok)
        assert store.get_agent(raw_tok) is None

    def test_authorize_success_and_failures(self) -> None:
        # Use default_store for tools.authorize tests
        tok = "test-auth-cop-token"
        default_store.register_token("cop", tok)

        # Successful authorization
        assert authorize(tok) == "cop"
        assert authorize(tok, "cop") == "cop"

        # Failure: agent mismatch
        with pytest.raises(ValueError, match="Token does not belong to thief"):
            authorize(tok, "thief")

        # Failure: unknown token
        with pytest.raises(ValueError, match="Invalid or missing token"):
            authorize("unknown-token")

        # Failure: revoked token
        default_store.revoke(tok)
        with pytest.raises(ValueError, match="Invalid or missing token"):
            authorize(tok)
