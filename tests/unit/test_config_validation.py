"""Validation-error, secret-loading, and from_env tests for Config — T-P0-23 (part 2/2).

Covers:
- Invalid grid_size (not a list, too small) raises ValueError.
- Missing email.to raises ValueError.
- max_barriers > max_moves raises ValueError.
- Negative max_moves raises ValueError.
- Missing required secret raises OSError with the var name in the message.
- Optional missing secret returns None.
- Present secret returns its value.
- from_env respects the CONFIG_PATH env var.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cop_thief.shared.config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, content: str) -> Path:
    """Write *content* (dedented) to tmp_path/config.yaml and return the path."""
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestConfigValidation:
    def test_invalid_grid_size_not_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path, """\
            grid_size: 5
            max_moves: 25
            num_games: 6
            max_barriers: 5
            email:
              to: "x@y.com"
            """)
        with pytest.raises(ValueError):
            Config.from_yaml(p)

    def test_invalid_grid_size_too_small(self, tmp_path: Path) -> None:
        p = _write(tmp_path, """\
            grid_size: [1, 1]
            max_moves: 25
            num_games: 6
            max_barriers: 5
            email:
              to: "x@y.com"
            """)
        with pytest.raises(ValueError, match=">="):
            Config.from_yaml(p)

    def test_missing_email_to_raises(self, tmp_path: Path) -> None:
        p = _write(tmp_path, """\
            grid_size: [5, 5]
            max_moves: 25
            num_games: 6
            max_barriers: 5
            """)
        with pytest.raises(ValueError):
            Config.from_yaml(p)

    def test_max_barriers_exceeds_max_moves_raises(self, tmp_path: Path) -> None:
        p = _write(tmp_path, """\
            grid_size: [5, 5]
            max_moves: 3
            num_games: 6
            max_barriers: 10
            email:
              to: "x@y.com"
            """)
        with pytest.raises(ValueError, match="max_barriers"):
            Config.from_yaml(p)

    def test_negative_max_moves_raises(self, tmp_path: Path) -> None:
        p = _write(tmp_path, """\
            grid_size: [5, 5]
            max_moves: -1
            num_games: 6
            max_barriers: 0
            email:
              to: "x@y.com"
            """)
        with pytest.raises(ValueError):
            Config.from_yaml(p)


# ---------------------------------------------------------------------------
# Secret loading (T-P0-11)
# ---------------------------------------------------------------------------


class TestSecretLoading:
    def test_missing_required_secret_raises_os_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(OSError, match="LLM_API_KEY"):
            Config.load_secret("LLM_API_KEY", required=True)

    def test_missing_optional_secret_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OPTIONAL_VAR", raising=False)
        assert Config.load_secret("OPTIONAL_VAR", required=False) is None

    def test_present_secret_returns_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LLM_API_KEY", "sk-test123")
        assert Config.load_secret("LLM_API_KEY") == "sk-test123"

    def test_error_message_contains_var_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(OSError) as exc_info:
            Config.load_secret("LLM_API_KEY", required=True)
        assert "LLM_API_KEY" in str(exc_info.value)


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------


class TestConfigFromEnv:
    def test_from_env_respects_config_path(
        self, valid_config_yaml: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CONFIG_PATH", str(valid_config_yaml))
        cfg = Config.from_env()
        assert cfg.email.to == "test@example.com"
