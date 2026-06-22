"""Sub-model schemas for the Cop–Thief configuration.

Each class here is a Pydantic ``BaseModel`` describing one logical section
of ``config/config.yaml``.  They are imported by the root
:class:`~cop_thief.shared.config.Config` model.

Traces: FR-C1, FR-C2, PLAN §10.1, T-P0-09.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from cop_thief.constants import StartMode, Strategy


class ScoringConfig(BaseModel):
    """Per-sub-game point values."""

    cop_win: int = Field(20, ge=0, description="Points to cop on cop-win.")
    thief_win: int = Field(10, ge=0, description="Points to thief on thief-win.")
    cop_loss: int = Field(5, ge=0, description="Points to cop on cop-loss.")
    thief_loss: int = Field(5, ge=0, description="Points to thief on thief-loss.")


class LlmConfig(BaseModel):
    """LLM provider/model configuration (non-secret part)."""

    provider: Literal["openai", "anthropic", "gemini", "ollama"] = "openai"
    model: str = Field("gpt-4o-mini", min_length=1)
    timeout_s: int = Field(30, ge=1, le=300)
    base_url: str | None = None


class McpConfig(BaseModel):
    """URLs for the two MCP servers (non-secret; tokens come from env)."""

    cop_url: str = Field("http://localhost:8001", min_length=1)
    thief_url: str = Field("http://localhost:8002", min_length=1)


class GatekeeperConfig(BaseModel):
    """Gatekeeper tunables — all from config, no hard-coding."""

    rate_limit_per_target: float = Field(
        5.0, gt=0, description="Requests/second per target (token-bucket refill rate)."
    )
    max_retries: int = Field(3, ge=0, le=20)
    queue_size: int = Field(64, ge=1, le=4096)
    timeout_s: int = Field(30, ge=1, le=300)


class EmailConfig(BaseModel):
    """Email destination for the JSON report."""

    to: str = Field(..., min_length=1, description="Recipient email address.")


class NlpConfig(BaseModel):
    """Natural-language message behavior."""

    tone: Literal["balanced", "deceptive", "probing"] = "balanced"
    transcript_dir: str = Field("results", min_length=1)


class ReportConfig(BaseModel):
    """Final JSON report identity fields."""

    group_name: str = Field("TBD", min_length=1)
    students: list[str] = Field(default_factory=list)
    github_repo: str = Field("TBD", min_length=1)


# Re-export enums so callers can import from one place when needed.
__all__ = [
    "EmailConfig",
    "GatekeeperConfig",
    "LlmConfig",
    "McpConfig",
    "NlpConfig",
    "ReportConfig",
    "ScoringConfig",
    "StartMode",
    "Strategy",
]
