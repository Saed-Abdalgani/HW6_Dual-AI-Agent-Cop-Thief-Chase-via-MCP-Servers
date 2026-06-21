"""SDK facade — single public API for GUI, CLI, and external consumers.

All business logic is invoked through this facade.  GUI and CLI code
must **never** import from ``services``, ``orchestrator``, or
``mcp_servers`` directly.

Traces: NFR-7, PLAN §7, T-P3-13.
"""

from __future__ import annotations

from cop_thief.shared.config import Config


class CopThiefSDK:
    """Public API for running the Cop–Thief game.

    This is a stub that will be fully implemented in Phase P3 (T-P3-13).

    Args:
        config: The loaded and validated :class:`~cop_thief.shared.config.Config`.

    """

    def __init__(self, config: Config) -> None:
        """Initialize the SDK with a validated configuration."""
        self._config = config

    def run_full_game(self) -> None:
        """Run a full game (6 valid sub-games) and send the report email.

        To be implemented in Phase P3.
        """
        raise NotImplementedError("run_full_game — Phase P3")

    def run_sub_game(self) -> None:
        """Run a single sub-game and return its result.

        To be implemented in Phase P3.
        """
        raise NotImplementedError("run_sub_game — Phase P3")

    def get_state(self) -> None:
        """Return the current game state for GUI rendering.

        To be implemented in Phase P3.
        """
        raise NotImplementedError("get_state — Phase P3")

    def health_check(self) -> None:
        """Return reachability status of MCP servers and LLM.

        To be implemented in Phase P3.
        """
        raise NotImplementedError("health_check — Phase P3")
