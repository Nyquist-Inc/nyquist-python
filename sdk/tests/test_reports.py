"""Reports sub-client tests. Fixtures mirror the endpoint contract the API serves."""
from __future__ import annotations

import json

import httpx

from .conftest import make_client

# ── save ──────────────────────────────────────────────────────────────────


def test_save_posts_strategy_report_request_returns_key():
    """41-03-SUMMARY POST /api/reports/save -> {saved: true, key: <bucket-prefixed>}."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"saved": True, "key": "nyquist-reports/u1/2026/Q3/report_123.html"},
        )

    out = make_client(handler).reports.save(
        title="My research", returns=[0.1, 0.2], metrics={"var": 0.02}
    )

    assert seen["path"] == "/api/reports/save"
    assert seen["body"] == {
        "title": "My research",
        "returns": [0.1, 0.2],
        "metrics": {"var": 0.02},
        "weights": None,
        "benchmark_returns": None,
    }
    assert out["saved"] is True
    assert out["key"] == "nyquist-reports/u1/2026/Q3/report_123.html"


def test_save_forwards_optional_weights_and_benchmark():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"saved": True, "key": "nyquist-reports/x"})

    make_client(handler).reports.save(
        title="X",
        returns=[0.1],
        metrics={},
        weights={"NVDA": 1.0},
        benchmark_returns=[0.05],
    )
    assert seen["body"]["weights"] == {"NVDA": 1.0}
    assert seen["body"]["benchmark_returns"] == [0.05]


# ── list ──────────────────────────────────────────────────────────────────


def test_list_returns_reports_envelope():
    """41-03-SUMMARY GET /api/reports/list -> {reports: [{key,size,last_modified}]}."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/reports/list"
        return httpx.Response(
            200,
            json={
                "reports": [
                    {
                        "key": "nyquist-reports/u1/2026/Q3/report_123.html",
                        "size": 512,
                        "last_modified": "2026-07-12 00:00:00",
                    }
                ]
            },
        )

    out = make_client(handler).reports.list()
    assert out == [
        {
            "key": "nyquist-reports/u1/2026/Q3/report_123.html",
            "size": 512,
            "last_modified": "2026-07-12 00:00:00",
        }
    ]


def test_list_empty_returns_empty_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"reports": []})

    out = make_client(handler).reports.list()
    assert out == []


# ── download_url ─────────────────────────────────────────────────────────


def test_download_url_returns_url_string():
    """41-03-SUMMARY GET /api/reports/download?key=... -> {url: <presigned>}."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/reports/download"
        assert dict(request.url.params)["key"] == "nyquist-reports/u1/2026/Q3/report_123.html"
        return httpx.Response(200, json={"url": "https://s3.example/presigned"})

    url = make_client(handler).reports.download_url(
        "nyquist-reports/u1/2026/Q3/report_123.html"
    )
    assert url == "https://s3.example/presigned"
