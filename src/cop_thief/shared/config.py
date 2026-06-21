"""Root configuration model for the Cop–Thief MCP system.

Loads ``config/config.yaml`` (or a path from the ``CONFIG_PATH`` env var),
validates all keys/ranges using Pydantic, and exposes a single typed
:class:`Config` object.  Secrets are **always** sourced from environment
variables — never from the config file itself.

Sub-model schemas live in :mod:`cop_thief.shared._config_schemas`.

Traces: FR-C1, FR-C2, FR-C3, T-P0-08, T-P0-09, T-P0-10, T-P0-11.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from cop_thief.constants import StartMode, Strategy
from cop_thief.shared._config_schemas import (
    EmailConfig,
    GatekeeperConfig,
    LlmConfig,
    McpConfig,
    ScoringConfig,
)

# Re-export sub-schemas so existing imports keep working.
__all__ = [
    "Config",
    "EmailConfig",
    "GatekeeperConfig",
    "LlmConfig",
    "McpConfig",
    "ScoringConfig",
]


class Config(BaseModel):
    """Typed, validated runtime configuration.

    All tunables come from ``config/config.yaml``; secrets come from env vars.
    Provides class-method loaders for convenience.
    """

    # Board
    grid_size: tuple[int, int] = Field((5, 5))
    max_moves: int = Field(25, ge=1)
    num_games: int = Field(6, ge=1)
    max_barriers: int = Field(5, ge=0)

    # Scoring
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)

    # Rules
    start_mode: StartMode = StartMode.RANDOM
    thief_moves_first: bool = True
    discount_gamma: float = Field(0.95, ge=0.0, le=1.0)

    # Strategy
    strategy: Strategy = Strategy.HEURISTIC

    # LLM / MCP / Gatekeeper / Email
    llm: LlmConfig = Field(default_factory=LlmConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)
    gatekeeper: GatekeeperConfig = Field(default_factory=GatekeeperConfig)
    email: EmailConfig

    # Misc
    timezone: str = "UTC"
    seed: int | None = None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("grid_size", mode="before")
    @classmethod
    def _validate_grid_size(cls, v: object) -> tuple[int, int]:
        """Ensure grid_size is a 2-element list/tuple of positive ints."""
        if not isinstance(v, (list, tuple)) or len(v) != 2:
            msg = "grid_size must be a 2-element list [rows, cols]."
            raise ValueError(msg)
        rows, cols = int(v[0]), int(v[1])
        if rows < 2 or cols < 2:  # noqa: PLR2004
            msg = "grid_size rows and cols must each be >= 2."
            raise ValueError(msg)
        return (rows, cols)

    @model_validator(mode="after")
    def _validate_cross_fields(self) -> Config:
        """Cross-field invariants that span multiple keys."""
        if self.max_barriers > self.max_moves:
            msg = (
                f"max_barriers ({self.max_barriers}) cannot exceed "
                f"max_moves ({self.max_moves})."
            )
            raise ValueError(msg)
        return self

    # ------------------------------------------------------------------
    # Secrets (T-P0-11) — loaded from env vars, not config
    # ------------------------------------------------------------------

    @classmethod
    def load_secret(cls, env_var: str, *, required: bool = True) -> str | None:
        """Return the value of an env var; raise :class:`OSError` if missing and required.

        Secrets are never logged.
        """
        value = os.environ.get(env_var)
        if required and not value:
            msg = (
                f"Required secret '{env_var}' is not set. "
                f"See .env-example for the full list of required env vars."
            )
            raise OSError(msg)
        return value

    # ------------------------------------------------------------------
    # Factory loaders
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load and validate config from a YAML file.

        Args:
            path: Absolute or relative path to the YAML config file.

        Returns:
            A fully validated :class:`Config` instance.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the YAML content fails validation.

        """
        path = Path(path)
        if not path.exists():
            msg = f"Config file not found: {path}"
            raise FileNotFoundError(msg)
        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return cls.model_validate(raw)

    @classmethod
    def from_env(cls) -> Config:
        """Load config from the path given by the ``CONFIG_PATH`` env var.

        Falls back to ``config/config.yaml`` when ``CONFIG_PATH`` is not set.
        """
        config_path = os.environ.get("CONFIG_PATH", "config/config.yaml")
        return cls.from_yaml(config_path)
