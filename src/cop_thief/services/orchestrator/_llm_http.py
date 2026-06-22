"""HTTP calls to LLM providers (OpenAI-compatible).

Traces: FR-LLM1/2, PLAN §13, T-P3-03.
"""

from __future__ import annotations

import os

import httpx

from cop_thief.shared._config_schemas import LlmConfig


def _resolve_base_url(cfg: LlmConfig) -> str:
    """Return the provider base URL from config or sensible defaults."""
    if cfg.base_url:
        return cfg.base_url.rstrip("/")
    defaults = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "ollama": "http://localhost:11434/v1",
    }
    return defaults.get(cfg.provider, "https://api.openai.com/v1")


async def call_llm_api(cfg: LlmConfig, api_key: str, prompt: str) -> str:
    """Call the configured LLM provider and return raw text content."""
    base = _resolve_base_url(cfg)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if cfg.provider == "anthropic":
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    payload: dict = {
        "model": cfg.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    if cfg.provider == "openai" or cfg.provider == "ollama":
        payload["response_format"] = {"type": "json_object"}
    url = f"{base}/chat/completions"
    if cfg.provider == "anthropic":
        url = f"{base}/messages"
        payload = {
            "model": cfg.model,
            "max_tokens": 256,
            "messages": [{"role": "user", "content": prompt}],
        }
    async with httpx.AsyncClient(timeout=float(cfg.timeout_s)) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    if cfg.provider == "anthropic":
        blocks = data.get("content", [])
        return blocks[0].get("text", "") if blocks else ""
    choices = data.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return message.get("content", "")


def load_api_key() -> str:
    """Load the LLM API key from environment."""
    return os.environ.get("LLM_API_KEY", "")
