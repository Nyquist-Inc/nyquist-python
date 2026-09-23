"""The stdio MCP server, driven in-process by the SDK's own client (no network).

``Client(server)`` speaks real MCP to the server object — tool listing, schema
validation, errors — so these tests see what Claude or Cursor would see.
"""
from __future__ import annotations

import json

import anyio
import httpx
import pytest
from mcp.client import Client

from nyquist_mcp.server import INSTRUCTIONS, build_server

pytestmark = pytest.mark.anyio

EXPECTED_TOOLS = {
    "nyquist_quote",
    "nyquist_price_history",
    "nyquist_value_at_risk",
    "nyquist_ask",
    "nyquist_bull_bear_debate",
    "nyquist_search_tools",
    "nyquist_describe_tool",
    "nyquist_call_tool",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _server(handler, api_key="nyquist_k"):
    return build_server(
        base_url="https://api.test", api_key=api_key, transport=httpx.MockTransport(handler)
    )


def _never(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"no request expected, got {request.url}")


async def _call(server, name, arguments=None, progress=None):
    async with Client(server) as client:
        return await client.call_tool(name, arguments or {}, progress_callback=progress)


def _text(result) -> str:
    return " ".join(getattr(block, "text", "") for block in result.content)


# ── listing ──────────────────────────────────────────────────────────────────


async def test_lists_every_tool_read_only_with_described_parameters():
    async with Client(_server(_never)) as client:
        listed = (await client.list_tools()).tools
    assert {t.name for t in listed} == EXPECTED_TOOLS
    for tool in listed:
        assert tool.description, tool.name
        if tool.name == "nyquist_call_tool":
            # Runs whatever governed tool it is named: no read-only claim.
            assert tool.annotations.read_only_hint is False
            assert tool.annotations.destructive_hint is None
            continue
        assert tool.annotations.read_only_hint is True, tool.name
        assert tool.annotations.destructive_hint is False, tool.name
    debate = next(t for t in listed if t.name == "nyquist_bull_bear_debate")
    # The injected Context is not a parameter the model must fill.
    assert set(debate.input_schema["properties"]) == {"ticker", "rounds", "language"}


def test_instructions_make_no_claim_the_tools_cannot_back():
    lowered = INSTRUCTIONS.lower()
    for claim in ("impossible", "hallucination", "guarantee", "ai-powered"):
        assert claim not in lowered


# ── research tools ───────────────────────────────────────────────────────────


async def test_quote_sends_the_callers_key_and_returns_the_payload():
    seen = {}

    def handler(request):
        seen["key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json={"ticker": "NVDA", "price": 181.2})

    result = await _call(_server(handler), "nyquist_quote", {"ticker": "NVDA"})
    assert not result.is_error
    assert result.structured_content == {"ticker": "NVDA", "price": 181.2}
    assert seen["key"] == "nyquist_k"


async def test_price_history_serialises_dates_and_reports_empty_honestly():
    bars = {"ticker": "NVDA", "source": "golden",
            "bars": [{"date": "2026-09-22", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 9}]}
    result = await _call(_server(lambda r: httpx.Response(200, json=bars)),
                         "nyquist_price_history", {"ticker": "NVDA", "days": 5})
    body = result.structured_content
    assert body["n_bars"] == 1 and body["source"] == "golden"
    assert body["bars"][0]["date"].startswith("2026-09-22")

    empty = await _call(_server(lambda r: httpx.Response(200, json={"ticker": "ZZ", "bars": []})),
                        "nyquist_price_history", {"ticker": "ZZ"})
    assert empty.structured_content["bars"] == [] and empty.structured_content["n_bars"] == 0


async def test_value_at_risk_builds_the_date_window():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"var": -0.021, "cvar": -0.03})

    result = await _call(_server(handler), "nyquist_value_at_risk",
                         {"symbols": ["NVDA", "AAPL"], "weights": [0.6, 0.4], "lookback_days": 60})
    assert result.structured_content == {"var": -0.021, "cvar": -0.03}
    assert seen["body"]["symbols"] == ["NVDA", "AAPL"]
    assert seen["body"]["method"] == "historical"
    assert seen["body"]["start_date"] < seen["body"]["end_date"]


async def test_schema_violation_is_rejected_before_any_request():
    result = await _call(_server(_never), "nyquist_value_at_risk",
                         {"symbols": ["NVDA"], "confidence": 1.5})
    assert result.is_error


async def test_bull_bear_debate_reports_progress_per_turn():
    frames = [
        ("agent_done", {"side": "bull", "round": 1, "text": "up"}),
        ("agent_done", {"side": "bear", "round": 1, "text": "down"}),
        ("agent_done", {"side": "judge", "text": "hold"}),
        ("debate_done", {"verdict": "hold"}),
    ]
    body = "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in frames)
    progress: list[tuple[float, float | None]] = []

    async def on_progress(value, total, message):
        progress.append((value, total))

    result = await _call(
        _server(lambda r: httpx.Response(200, headers={"content-type": "text/event-stream"},
                                         content=body.encode())),
        "nyquist_bull_bear_debate", {"ticker": "nvda", "rounds": 1}, progress=on_progress,
    )
    await anyio.sleep(0)
    debate = result.structured_content
    assert debate["complete"] is True and debate["verdict"] == "hold"
    assert debate["instrument"] == "NVDA"
    assert [t["side"] for t in debate["turns"]] == ["bull", "bear", "judge"]
    assert progress == [(1, 3), (2, 3), (3, 3)]


# ── errors ───────────────────────────────────────────────────────────────────


async def test_platform_refusal_reaches_the_model_with_its_reason():
    result = await _call(
        _server(lambda r: httpx.Response(503, json={"detail": "agents runtime disabled"})),
        "nyquist_bull_bear_debate", {"ticker": "NVDA"},
    )
    assert result.is_error
    assert "agents runtime disabled" in _text(result)
    assert "HTTP 503" in _text(result)


async def test_missing_key_is_a_tool_error_naming_what_to_set():
    server = _server(_never, api_key=None)
    async with Client(server) as client:
        assert len((await client.list_tools()).tools) == len(EXPECTED_TOOLS)
        result = await client.call_tool("nyquist_quote", {"ticker": "NVDA"})
    assert result.is_error
    assert "NYQUIST_API_KEY" in _text(result)


# ── governed surface ─────────────────────────────────────────────────────────


async def test_search_tools_says_switched_off_instead_of_no_match():
    result = await _call(
        _server(lambda r: httpx.Response(200, json={"query": "x", "results": [],
                                                    "total_available": 0, "enabled": False})),
        "nyquist_search_tools", {"query": "yield curve"},
    )
    body = result.structured_content
    assert body["enabled"] is False
    assert "not 'no match'" in body["message"]


async def test_search_describe_call_round_trip():
    tool = {"tool_id": "api.zcyc.get", "path": "/api/zcyc/", "method": "GET",
            "description": "Zero-coupon curve", "parameters_schema": {"type": "object"},
            "requires": "none", "reason": "read"}

    def handler(request):
        path = request.url.path
        if path == "/api/ontology/tools/search":
            return httpx.Response(200, json={"query": "curve", "results": [tool],
                                             "total_available": 1400, "enabled": True})
        if path == "/api/ontology/tools/api.zcyc.get":
            return httpx.Response(200, json=tool)
        if path == "/api/ontology/tools/api.zcyc.get/execute":
            assert json.loads(request.content) == {"parameters": {"date": "2026-09-22"}}
            return httpx.Response(200, json={"result": {"points": [[1, 0.041]]}})
        raise AssertionError(path)

    server = _server(handler)
    found = (await _call(server, "nyquist_search_tools", {"query": "curve"})).structured_content
    assert found["results"][0]["tool_id"] == "api.zcyc.get"
    assert "parameters_schema" not in found["results"][0]  # search stays small; describe has it
    described = (await _call(server, "nyquist_describe_tool", {"tool_id": "api.zcyc.get"}))
    assert described.structured_content["parameters_schema"] == {"type": "object"}
    called = await _call(server, "nyquist_call_tool",
                         {"tool_id": "api.zcyc.get", "parameters": {"date": "2026-09-22"}})
    assert called.structured_content == {"tool_id": "api.zcyc.get", "result": {"points": [[1, 0.041]]}}


# ── debate: cut stream, failing progress, cancellation ───────────────────────


def _sse_body(*frames):
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in frames).encode()


async def test_a_cut_stream_reports_ended_false():
    body = _sse_body(("agent_done", {"side": "bull", "round": 1, "text": "up"}))
    result = await _call(
        _server(lambda r: httpx.Response(200, headers={"content-type": "text/event-stream"},
                                         content=body)),
        "nyquist_bull_bear_debate", {"ticker": "NVDA", "rounds": 1},
    )
    debate = result.structured_content
    assert debate["complete"] is False and debate["ended"] is False
    assert [t["side"] for t in debate["turns"]] == ["bull"]


class _BrokenProgress:
    async def report_progress(self, *args, **kwargs):
        raise RuntimeError("client went away")


async def test_a_failing_progress_report_does_not_lose_the_debate():
    body = _sse_body(("agent_done", {"side": "judge", "text": "hold"}),
                     ("debate_done", {"verdict": "hold"}))
    server = _server(lambda r: httpx.Response(200, headers={"content-type": "text/event-stream"},
                                              content=body))
    fn = server._tool_manager.get_tool("nyquist_bull_bear_debate").fn
    debate = await fn(ticker="NVDA", ctx=_BrokenProgress(), rounds=1, language="en")
    assert debate["verdict"] == "hold"


async def test_cancelling_the_debate_returns_at_once_and_stops_the_stream():
    import threading
    import time

    release = threading.Event()
    consumed = []

    def handler(request):
        release.wait(5)  # the platform is still thinking
        return httpx.Response(200, headers={"content-type": "text/event-stream"},
                              content=_sse_body(("agent_done", {"side": "bull", "text": "up"}),
                                                ("debate_done", {"verdict": "hold"})))

    class _Ctx:
        async def report_progress(self, *args, **kwargs):
            consumed.append(args)

    fn = _server(handler)._tool_manager.get_tool("nyquist_bull_bear_debate").fn
    started = time.monotonic()
    with anyio.move_on_after(0.2):
        await fn(ticker="NVDA", ctx=_Ctx(), rounds=1, language="en")
    assert time.monotonic() - started < 1.0  # did not wait for the platform
    release.set()
    await anyio.sleep(0.2)
    assert consumed == []  # the abandoned worker left at its first turn
