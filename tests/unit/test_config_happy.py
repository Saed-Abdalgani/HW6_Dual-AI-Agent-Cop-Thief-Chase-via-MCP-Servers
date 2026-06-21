"""Happy-path and file-not-found tests for Config loading — T-P0-23 (part 1/2).

Covers:
- Valid YAML → Config object with correct field values.
- Missing config file raises FileNotFoundError.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cop_thief.shared.config import Config


class TestConfigHappyPath:
    def test_load_from_yaml_returns_config(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert isinstance(cfg, Config)

    def test_grid_size_parsed(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.grid_size == (5, 5)

    def test_max_moves(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.max_moves == 25

    def test_num_games(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.num_games == 6

    def test_max_barriers(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.max_barriers == 5

    def test_scoring_values(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.scoring.cop_win == 20
        assert cfg.scoring.thief_win == 10
        assert cfg.scoring.cop_loss == 5
        assert cfg.scoring.thief_loss == 5

    def test_llm_provider(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.llm.provider == "openai"

    def test_mcp_urls(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.mcp.cop_url == "http://localhost:8001"
        assert cfg.mcp.thief_url == "http://localhost:8002"

    def test_gatekeeper_queue_size(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.gatekeeper.queue_size == 64

    def test_email_to(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.email.to == "test@example.com"

    def test_seed(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.seed == 42

    def test_timezone(self, valid_config_yaml: Path) -> None:
        cfg = Config.from_yaml(valid_config_yaml)
        assert cfg.timezone == "UTC"


class TestConfigFileNotFound:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            Config.from_yaml(tmp_path / "nonexistent.yaml")
