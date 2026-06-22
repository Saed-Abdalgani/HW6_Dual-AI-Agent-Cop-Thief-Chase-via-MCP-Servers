"""CLI entry point — runs a full autonomous game via CopThiefSDK.

Invoke with::

    uv run cop-thief

Traces: AC-2, T-P3-14.
"""

from __future__ import annotations

import sys

from cop_thief.sdk.facade import CopThiefSDK
from cop_thief.shared.config import Config
from cop_thief.shared.logging import get_logger

_log = get_logger(__name__)


def main() -> None:
    """Run a full autonomous game (6 valid sub-games) with zero manual steps."""
    try:
        config = Config.from_env()
        sdk = CopThiefSDK(config, use_direct_mcp=True)
        report = sdk.run_full_game()
        _log.info(
            "Game complete: %d sub-games, cop=%d thief=%d",
            report.sub_games_played,
            report.cop_total,
            report.thief_total,
        )
        print(  # noqa: T201
            f"Done — {report.sub_games_played} valid sub-games. "
            f"Totals: cop={report.cop_total}, thief={report.thief_total}",
        )
    except Exception as exc:  # noqa: BLE001
        _log.exception("cop-thief run failed.")
        print(f"Error: {exc}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
