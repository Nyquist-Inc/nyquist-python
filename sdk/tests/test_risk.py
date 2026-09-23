"""Risk sub-client: method/path/body shaping."""
from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from nyquist import NyquistError

from .conftest import make_client


def test_var_posts_returns_and_method():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"var": 0.031, "cvar": 0.045, "method": "historical"})

    out = make_client(handler).risk.var(
        [0.01, -0.02, 0.005, -0.01], method="historical", confidence=0.99
    )
    assert seen["path"] == "/api/risk/var"
    assert seen["body"]["method"] == "historical"
    assert seen["body"]["confidence"] == 0.99
    assert seen["body"]["returns"] == [0.01, -0.02, 0.005, -0.01]
    # seed defaults to None and must be dropped from the body
    assert "seed" not in seen["body"]
    assert out["var"] == 0.031


def test_portfolio_var_zips_weights():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"var_value": 12000.0, "var_pct": 0.012})

    out = make_client(handler).risk.portfolio_var(
        ["NVDA", "AAPL"],
        [0.6, 0.4],
        {"NVDA": [0.01, -0.02], "AAPL": [0.0, 0.01]},
        confidence_level=0.95,
    )
    assert seen["path"] == "/api/risk/portfolio-var"
    assert seen["body"]["portfolio_weights"] == {"NVDA": 0.6, "AAPL": 0.4}
    assert seen["body"]["returns_data"]["NVDA"] == [0.01, -0.02]
    assert seen["body"]["confidence_level"] == 0.95
    assert out["var_value"] == 12000.0


def test_portfolio_var_length_mismatch_raises():
    client = make_client(lambda r: httpx.Response(200, json={}))
    with pytest.raises(NyquistError):
        client.risk.portfolio_var(["A", "B"], [1.0], {})


def test_symbol_var_path_and_dates():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"var": 0.02, "data_source": "golden_record"})

    out = make_client(handler).risk.symbol_var(
        ["SPY", "QQQ"], "2026-01-01T00:00:00", "2026-04-01T00:00:00", weights=[0.5, 0.5]
    )
    assert seen["path"] == "/api/risk/symbol/var"
    assert seen["body"]["symbols"] == ["SPY", "QQQ"]
    assert seen["body"]["start_date"] == "2026-01-01T00:00:00"
    assert seen["body"]["weights"] == [0.5, 0.5]
    assert out["data_source"] == "golden_record"
