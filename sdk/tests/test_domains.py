"""Domain sub-client tests: stress, backtest, macro, crypto, agents, ledger (41-02)."""
from __future__ import annotations

import json
from typing import Any

import httpx
import pandas as pd
import pytest

from nyquist import NyquistError

from .conftest import make_client

# ── Stress ────────────────────────────────────────────────────────────────


def test_stress_submit_returns_job_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/stress/submit"
        assert json.loads(request.content) == {
            "portfolio": {"NVDA": 0.5, "AAPL": 0.5},
            "scenario": "rates_up_200bp",
        }
        return httpx.Response(202, json={"job_id": "job-1", "status": "enqueued"})

    job_id = make_client(handler).stress.submit(
        {"portfolio": {"NVDA": 0.5, "AAPL": 0.5}, "scenario": "rates_up_200bp"}
    )
    assert job_id == "job-1"


def test_stress_job_returns_hash_state():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/stress/job/job-1"
        return httpx.Response(200, json={"status": "running", "progress": 0.4})

    out = make_client(handler).stress.job("job-1")
    assert out["status"] == "running"


def test_stress_run_polls_until_completed():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/stress/submit":
            return httpx.Response(202, json={"job_id": "job-2", "status": "enqueued"})
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(200, json={"status": "running", "progress": 0.5})
        return httpx.Response(
            200,
            json={"status": "completed", "progress": 1.0, "result": {"var": 0.05}},
        )

    result = make_client(handler).stress.run(
        {"portfolio": {"NVDA": 1.0}, "scenario": "x"}, poll_interval=0.001
    )
    assert result == {"var": 0.05}
    assert calls["n"] == 3


def test_stress_run_raises_on_failed_job():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/stress/submit":
            return httpx.Response(202, json={"job_id": "job-3", "status": "enqueued"})
        return httpx.Response(200, json={"status": "failed", "error": "boom"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).stress.run(
            {"portfolio": {}, "scenario": "x"}, poll_interval=0.001
        )
    assert "boom" in exc.value.detail


def test_stress_run_raises_on_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/stress/submit":
            return httpx.Response(202, json={"job_id": "job-4", "status": "enqueued"})
        return httpx.Response(200, json={"status": "running", "progress": 0.1})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).stress.run(
            {"portfolio": {}, "scenario": "x"}, poll_interval=0.001, timeout=0.005
        )
    assert "did not complete" in exc.value.detail


def test_stress_scenarios_returns_list():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/stress/historical-scenarios"
        return httpx.Response(200, json={"scenarios": [{"key": "gfc_2008"}]})

    out = make_client(handler).stress.scenarios()
    assert out["scenarios"][0]["key"] == "gfc_2008"


# ── Backtest ──────────────────────────────────────────────────────────────


def test_backtest_run_sync_posts_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/backtest/run"
        assert json.loads(request.content)["mu"] == [0.1, 0.2]
        return httpx.Response(200, json={"sharpe": 1.2})

    out = make_client(handler).backtest.run(
        {"mu": [0.1, 0.2], "cov_matrix": [[1, 0], [0, 1]], "risk_free_rate": 0.02, "gamma": 2}
    )
    assert out["sharpe"] == 1.2


def test_backtest_historical_posts_payload():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/backtest/historical"
        return httpx.Response(200, json={"total_return": 0.15})

    out = make_client(handler).backtest.historical(
        {"historical_prices": [[100.0, 50.0], [101.0, 51.0]]}
    )
    assert out["total_return"] == 0.15


def test_backtest_submit_and_job_mirror_stress():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/backtest/submit":
            assert json.loads(request.content) == {
                "kind": "symbol_historical",
                "params": {"symbols": ["NVDA"]},
            }
            return httpx.Response(202, json={"job_id": "bt-1", "status": "enqueued"})
        assert request.url.path == "/api/backtest/job/bt-1"
        return httpx.Response(200, json={"status": "running"})

    nq = make_client(handler)
    job_id = nq.backtest.submit(
        {"kind": "symbol_historical", "params": {"symbols": ["NVDA"]}}
    )
    assert job_id == "bt-1"
    assert nq.backtest.job("bt-1")["status"] == "running"


def test_backtest_run_async_polls_to_completion():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/backtest/submit":
            return httpx.Response(202, json={"job_id": "bt-2", "status": "enqueued"})
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(200, json={"status": "running"})
        return httpx.Response(
            200, json={"status": "completed", "result": {"cagr": 0.09}}
        )

    result = make_client(handler).backtest.run_async(
        {"kind": "symbol_historical", "params": {}}, poll_interval=0.001
    )
    assert result == {"cagr": 0.09}


# ── Macro ─────────────────────────────────────────────────────────────────


def test_macro_fred_builds_date_indexed_frame():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "series_id": "DGS10",
                "count": 2,
                "observations": [
                    {"date": "2026-01-02", "value": 4.5},
                    {"date": "2026-01-01", "value": 4.4},
                ],
                "provider": "fred",
            },
        )

    df = make_client(handler).macro.fred("DGS10", limit=10)
    assert seen["path"] == "/api/macro-data/fred/series"
    assert seen["query"]["series_id"] == "DGS10"
    assert seen["query"]["limit"] == "10"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.index) == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")]
    assert list(df.columns) == ["value"]
    assert df.loc["2026-01-02", "value"] == 4.5


def test_macro_fred_empty_returns_empty_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"series_id": "ZZZ", "count": 0, "observations": [], "provider": "fred"}
        )

    df = make_client(handler).macro.fred("ZZZ")
    assert df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ["value"]


def test_macro_ecb_history_shapes_rates():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/macro-data/ecb/history"
        assert dict(request.url.params)["start"] == "2026-01-01"
        return httpx.Response(
            200,
            json={
                "base": "EUR",
                "start_date": "2026-01-01",
                "end_date": "2026-01-02",
                "rates": {
                    "2026-01-01": {"USD": 1.08},
                    "2026-01-02": {"USD": 1.09},
                },
                "provider": "frankfurter",
            },
        )

    df = make_client(handler).macro.ecb_history(start="2026-01-01")
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ["USD"]
    assert df.loc["2026-01-02", "USD"] == 1.09


def test_macro_cbr_key_rate_returns_dict():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/macro-data/cbr/key-rate"
        return httpx.Response(200, json={"current_rate": 16.0, "history": []})

    out = make_client(handler).macro.cbr_key_rate()
    assert out["current_rate"] == 16.0


# ── Crypto ────────────────────────────────────────────────────────────────


def test_crypto_markets_builds_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/crypto-data/coingecko/markets"
        return httpx.Response(
            200,
            json=[
                {"id": "bitcoin", "symbol": "btc", "current_price": 65000.0},
                {"id": "ethereum", "symbol": "eth", "current_price": 3200.0},
            ],
        )

    df = make_client(handler).crypto.markets(vs_currency="usd")
    assert len(df) == 2
    assert "current_price" in df.columns


def test_crypto_markets_empty_returns_empty_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    df = make_client(handler).crypto.markets()
    assert df.empty


def test_crypto_chart_builds_date_indexed_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/crypto-data/coingecko/coin/bitcoin/chart"
        assert dict(request.url.params)["days"] == "30"
        return httpx.Response(
            200,
            json={
                "coin_id": "bitcoin",
                "vs_currency": "usd",
                "prices": [[1767225600000, 64000.0], [1767312000000, 65000.0]],
                "market_caps": [[1767225600000, 1.2e12], [1767312000000, 1.25e12]],
                "total_volumes": [[1767225600000, 3e10], [1767312000000, 3.1e10]],
            },
        )

    df = make_client(handler).crypto.chart("bitcoin", days=30)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ["price", "market_cap", "total_volume"]
    assert df.iloc[0]["price"] == 64000.0


def test_crypto_chart_empty_returns_empty_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"coin_id": "x", "prices": []})

    df = make_client(handler).crypto.chart("x")
    assert df.empty
    assert list(df.columns) == ["price", "market_cap", "total_volume"]


def test_crypto_trending_and_global():
    def handler(request: httpx.Request) -> httpx.Response:
        if "trending" in request.url.path:
            return httpx.Response(200, json={"coins": []})
        return httpx.Response(200, json={"market_cap_usd": 2.5e12, "provider": "coingecko"})

    nq = make_client(handler)
    assert nq.crypto.trending() == {"coins": []}
    assert nq.crypto.global_stats()["provider"] == "coingecko"


# ── Agents ────────────────────────────────────────────────────────────────


def test_agents_list_returns_roster():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/agents/list"
        return httpx.Response(200, json=[{"id": "buffett", "name": "Buffett"}])

    out = make_client(handler).agents.list()
    assert out[0]["id"] == "buffett"


def test_agents_chat_posts_message_and_drops_none_session():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "agent_id": "buffett",
                "text": "hello back",
                "model_id": "nemotron-3",
                "provider": "nvidia_nim",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "voice_drift": [],
                "tool_calls": [],
            },
        )

    out = make_client(handler).agents.chat("buffett", "hello")
    assert seen["path"] == "/api/agents/buffett/chat"
    assert seen["body"] == {"message": "hello"}
    assert out["text"] == "hello back"
    assert out["agent_id"] == "buffett"


def test_agents_chat_forwards_session_id():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"agent_id": "buffett", "text": "ok"})

    make_client(handler).agents.chat("buffett", "hi", session_id="sess-1")
    assert seen["body"] == {"message": "hi", "session_id": "sess-1"}


# ── Execution Ledger ──────────────────────────────────────────────────────


def test_ledger_trades_builds_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/execution-ledger/trades"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": 1, "source": "OTC_P2P", "source_ref": "abc",
                        "account_id": "acct-1", "instrument": "USDT-USD",
                        "side": "buy", "quantity": "100", "price": "1.0",
                        "notional": "100", "currency": "USD", "venue": "desk",
                        "counterparty": "nyquist_desk", "status": "settled",
                        "executed_at": "2026-07-01T00:00:00+00:00",
                        "settlement_date": None, "details": {},
                    },
                ],
                "total": 1,
            },
        )

    df = make_client(handler).ledger.trades()
    assert len(df) == 1
    assert df.iloc[0]["instrument"] == "USDT-USD"


def test_ledger_trades_empty_returns_stable_columns():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": [], "total": 0})

    df = make_client(handler).ledger.trades()
    assert df.empty
    assert "instrument" in df.columns


def test_ledger_positions_builds_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/execution-ledger/positions"
        return httpx.Response(
            200,
            json=[
                {
                    "instrument": "NVDA", "source": "TRADFI", "net_quantity": "10",
                    "gross_notional": "1000", "net_notional": "1000", "trades": 2,
                    "last_price": "100", "last_executed_at": "2026-07-01T00:00:00+00:00",
                },
            ],
        )

    df = make_client(handler).ledger.positions()
    assert len(df) == 1
    assert df.iloc[0]["instrument"] == "NVDA"


def test_ledger_positions_empty_returns_stable_columns():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    df = make_client(handler).ledger.positions()
    assert df.empty
    assert "net_quantity" in df.columns


def test_ledger_reconciliation_sources_sync():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.url.path == "/api/execution-ledger/sync"
            return httpx.Response(200, json={"synced": True})
        if request.url.path.endswith("/reconciliation"):
            return httpx.Response(200, json={"OTC_P2P": {"ledger": 1, "origin": 1, "lag": 0}})
        return httpx.Response(200, json={"sources": ["OTC_P2P", "TRADFI", "NCCH", "RWA_PRIMARY"]})

    nq = make_client(handler)
    assert nq.ledger.reconciliation()["OTC_P2P"]["lag"] == 0
    assert "TRADFI" in nq.ledger.sources()["sources"]
    assert nq.ledger.sync()["synced"] is True
