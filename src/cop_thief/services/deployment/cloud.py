"""Cloud deployment helpers for MCP URL detection and hybrid wiring.

Traces: FR-MCP5, NFR-3, T-P7-04, T-P7-05.
"""

from __future__ import annotations

from urllib.parse import urlparse

from cop_thief.shared.config import Config

_PLACEHOLDER_MARKERS = ("replace-with", "example.com")


def is_deployed_url(url: str) -> bool:
    """Return True when *url* looks like a live HTTPS deployment."""
    lowered = url.lower()
    if not lowered.startswith("https://"):
        return False
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def cloud_urls_ready(config: Config) -> bool:
    """Return True when both MCP URLs are configured for cloud use."""
    return is_deployed_url(config.mcp.cop_url) and is_deployed_url(config.mcp.thief_url)


def resolve_mcp_wiring(config: Config) -> tuple[bool, bool]:
    """Return ``(use_direct_mcp, auto_launch_servers)`` for *config*."""
    hosts = _mcp_hosts(config)
    localhost = hosts <= {"localhost", "127.0.0.1"}

    if config.mcp.mode == "direct":
        return True, False
    if config.mcp.mode == "http":
        return False, bool(config.mcp.auto_launch and localhost)
    if cloud_urls_ready(config):
        return False, False
    if localhost:
        return True, False
    return False, False


def _mcp_hosts(config: Config) -> set[str | None]:
    """Return hostnames configured for both MCP endpoints."""
    return {
        urlparse(config.mcp.cop_url).hostname,
        urlparse(config.mcp.thief_url).hostname,
    }


def assert_hybrid_client_safe(config: Config) -> None:
    """Reject configs that would expose a local Ollama port in cloud hybrid mode."""
    if not cloud_urls_ready(config):
        return
    base = (config.llm.base_url or "").lower()
    if "11434" in base or "localhost" in base or "127.0.0.1" in base:
        msg = "Hybrid cloud mode must not publish local LLM/Ollama endpoints."
        raise ValueError(msg)
