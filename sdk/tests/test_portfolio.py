"""Portfolio sub-client: list -> DataFrame, get -> dict."""
from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from .conftest import make_client


def test_list_returns_dataframe():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(
            200,
            json=[
                {"plan_id": "p1", "status": "draft", "portfolio_id": "pf1"},
                {"plan_id": "p2", "status": "approved", "portfolio_id": "pf1"},
            ],
        )

    df = make_client(handler).portfolio.list(portfolio_id="pf1")
    assert seen["path"] == "/api/portfolio/plans"
    assert seen["query"]["portfolio_id"] == "pf1"
    assert isinstance(df, pd.DataFrame)
    assert list(df["plan_id"]) == ["p1", "p2"]


def test_list_empty_returns_empty_frame():
    df = make_client(lambda r: httpx.Response(200, json=[])).portfolio.list()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_get_returns_dict():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/portfolio/plans/p1"
        return httpx.Response(200, json={"plan_id": "p1", "status": "draft"})

    out = make_client(handler).portfolio.get("p1")
    assert out["plan_id"] == "p1"
