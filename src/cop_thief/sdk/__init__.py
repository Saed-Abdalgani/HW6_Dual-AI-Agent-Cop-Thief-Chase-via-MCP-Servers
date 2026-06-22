"""SDK facade — public API for GUI, CLI, and external consumers."""

from cop_thief.sdk._facade_types import FullGameReport, GameState, HealthStatus
from cop_thief.sdk.facade import CopThiefSDK

__all__ = ["CopThiefSDK", "FullGameReport", "GameState", "HealthStatus"]
