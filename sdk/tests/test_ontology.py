"""Ontology sub-client (the semantic layer): ask + semantic search."""
from __future__ import annotations

import json
from typing import Any

import httpx
import pandas as pd

from .conftest import make_client


def test_ask_posts_query_and_returns_answer_plus_rows():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "query": "largest exposure?",
                "intent": "aggregate",
                "n_results": 2,
                "answer": "Counterparty ACME is the largest exposure.",
                "results": [
                    {"object_id": "nq:counterparty:acme", "name": "ACME"},
                    {"object_id": "nq:counterparty:globex", "name": "Globex"},
                ],
                "model_id": "nim/llama",
                "provider": "nvidia_nim",
                "error": None,
            },
        )

    res = make_client(handler).ontology.ask("largest exposure?", language="en")
    assert seen["path"] == "/api/ontology/query/ask"
    assert seen["body"] == {"query": "largest exposure?", "language": "en"}
    assert res.answer.startswith("Counterparty ACME")
    assert res.intent == "aggregate"
    assert res.n_results == 2
    assert isinstance(res.rows, pd.DataFrame)
    assert list(res.rows["name"]) == ["ACME", "Globex"]
    assert str(res) == res.answer


def test_ask_degraded_in_band_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"query": "x", "n_results": 0, "answer": "",
                  "results": [], "error": "clickhouse unreachable"},
        )

    res = make_client(handler).ontology.ask("x")
    assert res.error == "clickhouse unreachable"
    assert res.rows.empty


def test_search_returns_object_plus_distance_frame():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json=[
                {"object": {"object_id": "nq:instrument:nvda", "kind": "instrument"},
                 "distance": 0.42},
                {"object": {"object_id": "nq:instrument:aapl", "kind": "instrument"},
                 "distance": 0.10},
            ],
        )

    df = make_client(handler).ontology.search("ai chips", k=5, kind="instrument")
    assert seen["path"] == "/api/ontology/search/semantic"
    assert seen["body"] == {"query": "ai chips", "k": 5, "kind": "instrument"}
    # sorted ascending by distance (nearest first)
    assert list(df["object_id"]) == ["nq:instrument:aapl", "nq:instrument:nvda"]
    assert list(df["distance"]) == [0.10, 0.42]


def test_search_empty_returns_empty_frame():
    df = make_client(lambda r: httpx.Response(200, json=[])).ontology.search("x")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
