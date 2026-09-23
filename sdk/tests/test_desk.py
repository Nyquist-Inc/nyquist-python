"""Desk: SSE parsing + the bull/bear debate (hermetic MockTransport)."""
from __future__ import annotations

import json

import httpx
import pytest

from nyquist import NyquistError
from nyquist._sse import parse_sse
from nyquist.desk import DEBATE_PATH

from .conftest import make_client


def _frame(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream(*frames: str) -> httpx.Response:
    return httpx.Response(
        200, headers={"content-type": "text/event-stream"}, content="".join(frames).encode()
    )


_FULL = (
    _frame("debate_start", {"instrument": "NVDA", "rounds": 1}),
    _frame("agent_done",
           {"side": "bull", "round": 1, "agent_id": "a", "text": " up ", "error": None}),
    _frame("agent_done",
           {"side": "bear", "round": 1, "agent_id": "b", "text": "down", "error": None}),
    _frame("agent_done", {"side": "judge", "agent_id": "c", "text": "hold"}),
    _frame("debate_done", {"instrument": "NVDA", "verdict": "hold"}),
)


# ── parse_sse ────────────────────────────────────────────────────────────────


def test_parse_sse_pairs_event_with_json_data():
    lines = ["event: agent_done", 'data: {"side": "bull"}', "", ": keep-alive", ""]
    assert list(parse_sse(lines)) == [("agent_done", {"side": "bull"})]


def test_parse_sse_defaults_event_and_keeps_non_json_raw():
    assert list(parse_sse(["data: not json", ""])) == [("message", {"raw": "not json"})]


def test_parse_sse_flushes_a_final_frame_without_blank_line():
    assert list(parse_sse(["event: x", "data: {}"])) == [("x", {})]


def test_parse_sse_drops_a_frame_without_data():
    assert list(parse_sse(["event: orphan", ""])) == []


# ── debate ───────────────────────────────────────────────────────────────────


def test_debate_collects_turns_and_verdict():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        seen["accept"] = request.headers.get("accept")
        return _stream(*_FULL)

    landed = []
    debate = make_client(handler).desk.debate("NVDA", rounds=1, on_turn=landed.append)

    assert seen["path"] == DEBATE_PATH
    assert seen["body"] == {"instrument": "NVDA", "rounds": 1, "language": "en"}
    assert seen["accept"] == "text/event-stream"
    assert [t.side for t in debate.turns] == ["bull", "bear", "judge"]
    assert debate.turns[0].text == "up"
    assert debate.verdict == "hold" and debate.complete
    assert [t.side for t in landed] == ["bull", "bear", "judge"]


def test_debate_without_verdict_is_incomplete_not_invented():
    def handler(request: httpx.Request) -> httpx.Response:
        return _stream(
            _frame("agent_done",
                   {"side": "bull", "round": 1, "text": "", "error": "model timeout"}),
        )

    debate = make_client(handler).desk.debate("NVDA", rounds=1)
    assert not debate.complete
    assert debate.verdict == ""
    assert debate.failed_turns[0].error == "model timeout"
    assert debate.as_dict()["complete"] is False


def test_debate_passes_persona_overrides_only_when_set():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return _stream(*_FULL)

    make_client(handler).desk.debate("NVDA", judge_id="j", language="ru")
    assert seen["body"] == {"instrument": "NVDA", "rounds": 2, "language": "ru", "judge_id": "j"}


def test_debate_refusal_raises_with_server_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "agents runtime disabled"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).desk.debate("NVDA")
    assert exc.value.status_code == 503
    assert "agents runtime disabled" in exc.value.detail
