"""SDK facade — single public API for GUI, CLI, and external consumers.

Traces: NFR-7, PLAN §7, T-P3-13.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable

from cop_thief.mcp_servers import _state
from cop_thief.sdk._facade_types import FullGameReport, GameState, HealthStatus
from cop_thief.services.deployment.cloud import assert_hybrid_client_safe, resolve_mcp_wiring
from cop_thief.services.engine._lifecycle_types import SubGameResult
from cop_thief.services.nlp.transcript import TranscriptLogger
from cop_thief.services.orchestrator._mcp_direct import DirectMcpBackend
from cop_thief.services.orchestrator._mcp_launcher import McpServerLauncher
from cop_thief.services.orchestrator.estimator import OpponentEstimator
from cop_thief.services.orchestrator.game_loop import GameLoop
from cop_thief.services.orchestrator.llm_client import LlmClient
from cop_thief.services.orchestrator.mcp_client import McpClient
from cop_thief.services.orchestrator.turn_controller import TurnController
from cop_thief.services.orchestrator.validator import ActionValidator
from cop_thief.services.report.dispatch import ReportSender, dispatch_final_report
from cop_thief.services.strategy.factory import create_strategy
from cop_thief.shared.auth import default_store
from cop_thief.shared.config import Config
from cop_thief.shared.gatekeeper import Gatekeeper


class CopThiefSDK:
    """Public API for running the Cop–Thief game."""

    def __init__(
        self,
        config: Config,
        *,
        use_direct_mcp: bool | None = None,
        auto_launch_servers: bool | None = None,
        llm_caller: object | None = None,
        report_sender: ReportSender | None = None,
    ) -> None:
        """Initialize orchestrator wiring from *config*."""
        assert_hybrid_client_safe(config)
        direct, launch = resolve_mcp_wiring(config)
        if use_direct_mcp is None:
            use_direct_mcp = direct
        if auto_launch_servers is None:
            auto_launch_servers = launch
        self._config = config
        self._use_direct = use_direct_mcp
        self._auto_launch = auto_launch_servers
        self._gk = Gatekeeper(config.gatekeeper)
        self._report_sender = report_sender
        cop_tok = Config.load_secret("MCP_COP_TOKEN") or ""
        thief_tok = Config.load_secret("MCP_THIEF_TOKEN") or ""
        if cop_tok:
            default_store.register_token("cop", cop_tok)
        if thief_tok:
            default_store.register_token("thief", thief_tok)
        if use_direct_mcp:
            _state.clear_state_file()
        backend = DirectMcpBackend(cop_tok, thief_tok) if use_direct_mcp else None
        self._mcp = McpClient(config, self._gk, cop_tok, thief_tok, backend=backend)
        self._llm = LlmClient(config, self._gk, llm_caller=llm_caller)  # type: ignore[arg-type]
        self._estimator = OpponentEstimator(config.grid_size)
        self._strategy = create_strategy(config, self._llm)
        self._turn = TurnController(
            config,
            self._mcp,
            self._strategy,
            self._estimator,
            ActionValidator(),
            TranscriptLogger(config.nlp.transcript_dir),
        )
        self._loop = GameLoop(config, self._mcp, self._turn, random.Random(config.seed))
        self._state = GameState(
            grid_size=config.grid_size,
            max_barriers=config.max_barriers,
            idle=True,
        )

    @classmethod
    def from_env(cls, **kwargs: object) -> CopThiefSDK:
        """Build an SDK instance from ``CONFIG_PATH`` / ``config/config.yaml``."""
        return cls(Config.from_env(), **kwargs)  # type: ignore[arg-type]

    def _run_async(self, coro: object) -> object:
        return asyncio.run(coro)  # type: ignore[arg-type]

    def run_full_game(self, on_frame: Callable[[GameState], None] | None = None) -> FullGameReport:
        """Run 6 valid sub-games autonomously and return aggregated results."""
        if self._auto_launch and not self._use_direct:
            with McpServerLauncher(self._config):
                result = self._run_async(self._loop.run_full_game(on_frame=on_frame))
        else:
            result = self._run_async(self._loop.run_full_game(on_frame=on_frame))
        report_json, email = self._run_async(
            dispatch_final_report(self._config, self._gk, result, self._report_sender),
        )
        return FullGameReport.from_result(
            result,
            report_json=str(report_json),
            email=email,  # type: ignore[arg-type]
        )

    def run_sub_game(
        self,
        index: int = 1,
        on_frame: Callable[[GameState], None] | None = None,
    ) -> SubGameResult:
        """Run a single sub-game and return its result."""
        result = self._run_async(self._loop.run_sub_game(index, on_frame=on_frame))
        frames = self.get_replay_frames()
        if frames:
            self._state = frames[-1]
        return result  # type: ignore[return-value]

    def get_state(self) -> GameState:
        """Return the latest cached game state snapshot for GUI rendering."""
        return self._state

    def get_replay_frames(self) -> list[GameState]:
        """Return visual replay frames from the most recent sub-game."""
        return self._loop.snapshots

    async def _refresh_state(self) -> GameState:
        status = await self._mcp.game_status()
        cop = await self._mcp.verify_position("cop")
        thief = await self._mcp.verify_position("thief")
        self._state = GameState(
            cop_pos=tuple(cop["pos"]),
            thief_pos=tuple(thief["pos"]),
            barriers=[tuple(item) for item in status.get("barriers", [])],
            move_count=status.get("move_count", 0),
            barriers_used=status.get("barriers_used", 0),
            max_barriers=self._config.max_barriers,
            over=status.get("over", False),
            winner=status.get("winner"),
            scores=status.get("scores", {"cop": 0, "thief": 0}),
        )
        return self._state

    def health_check(self) -> HealthStatus:
        """Return reachability status of MCP servers and LLM."""
        mcp_status = self._run_async(self._mcp.health_check())  # type: ignore[assignment]
        llm_ok = self._run_async(self._llm.health_check())  # type: ignore[assignment]
        mcp_status.llm = bool(llm_ok)
        return mcp_status
