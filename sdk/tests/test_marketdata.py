"""Market-data sub-client: path/params + DataFrame shaping."""
from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from .conftest import make_client


def test_history_builds_date_indexed_ohlcv_frame():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "ticker": "NVDA",
                "source": "golden_market_data_v2",
                "count": 2,
                "bars": [
                    {"date": "2026-01-02", "open": 1.0, "high": 2.0,
                     "low": 0.5, "close": 1.5, "volume": 100.0},
                    {"date": "2026-01-01", "open": 0.9, "high": 1.8,
                     "low": 0.4, "close": 1.2, "volume": 90.0},
                ],
            },
        )

    df = make_client(handler).marketdata.history("NVDA", days=30)
    assert seen["path"] == "/api/market-data/history/NVDA"
    assert seen["query"]["lookback_days"] == "30"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.name == "date"
    # sorted ascending by date
    assert list(df.index) == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert df.loc["2026-01-02", "close"] == 1.5
    assert df.attrs["ticker"] == "NVDA"
    assert df.attrs["source"] == "golden_market_data_v2"


def test_history_source_param_forwarded():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"ticker": "AAPL", "source": "twse", "bars": []})

    make_client(handler).marketdata.history("AAPL", source="twse")
    assert seen["query"]["source"] == "twse"


def test_history_empty_returns_empty_frame():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ticker": "ZZZZ", "source": "x", "count": 0, "bars": []})

    df = make_client(handler).marketdata.history("ZZZZ")
    assert df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_price_returns_dict():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/market-data/stock/NVDA"
        return httpx.Response(200, json={"ticker": "NVDA", "price": 123.4})

    out = make_client(handler).marketdata.price("NVDA")
    assert out["price"] == 123.4


def test_fx_path_and_dict():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/market-data/currency/EUR/USD"
        return httpx.Response(200, json={"base": "EUR", "quote": "USD", "rate": 1.08})

    out = make_client(handler).marketdata.fx("EUR", "USD")
    assert out["rate"] == 1.08
