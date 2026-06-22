"""Unit tests for the HTTP shared state service."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from cop_thief.mcp_servers import state_server


@pytest.fixture()
def state_service(monkeypatch: pytest.MonkeyPatch) -> str:
    """Run the state HTTP service on a local ephemeral port."""
    monkeypatch.setenv("MCP_STATE_TOKEN", "state-test-token")
    monkeypatch.setenv("MCP_STATE_PORT", "8199")
    monkeypatch.setenv("MCP_STATE_HOST", "127.0.0.1")
    state_server._StateHandler.store = None
    thread = threading.Thread(target=state_server.main, daemon=True)
    thread.start()
    deadline = 3.0
    import time

    start = time.monotonic()
    while time.monotonic() - start < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8199/", timeout=0.5):  # noqa: S310
                pass
        except urllib.error.HTTPError as exc:
            if exc.code == 401:  # noqa: PLR2004
                return "http://127.0.0.1:8199"
        except OSError:
            time.sleep(0.1)
    pytest.fail("State service did not start.")


def test_state_service_put_and_get(state_service: str) -> None:
    body = json.dumps({"winner": "in_progress"}).encode()
    req = urllib.request.Request(  # noqa: S310
        f"{state_service}/",
        data=body,
        headers={
            "Authorization": "Bearer state-test-token",
            "Content-Type": "application/json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
        assert resp.status == 204  # noqa: PLR2004
    get_req = urllib.request.Request(  # noqa: S310
        f"{state_service}/",
        headers={"Authorization": "Bearer state-test-token"},
        method="GET",
    )
    with urllib.request.urlopen(get_req, timeout=5) as resp:  # noqa: S310
        data = json.loads(resp.read())
    assert data["winner"] == "in_progress"
