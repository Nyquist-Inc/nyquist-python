"""Escape-hatch tests: public get/post + multipart-capable _request (41-02)."""
from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from nyquist import NyquistError

from .conftest import make_client


def test_get_issues_query_and_drops_none():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json={"ok": True})

    out = make_client(handler).get("/api/x", foo=1, bar=None)
    assert seen["method"] == "GET"
    assert seen["path"] == "/api/x"
    assert seen["query"] == {"foo": "1"}
    assert "bar" not in seen["query"]
    assert out == {"ok": True}


def test_post_sends_json_body():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["content_type"] = request.headers.get("content-type")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"created": True})

    out = make_client(handler).post("/api/x", json={"a": 1})
    assert seen["method"] == "POST"
    assert seen["content_type"] == "application/json"
    assert seen["body"] == {"a": 1}
    assert out == {"created": True}


def test_post_files_issues_multipart_without_json_header_conflict():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content_type"] = request.headers.get("content-type", "")
        seen["body"] = request.content
        return httpx.Response(200, json={"uploaded": True})

    out = make_client(handler).post(
        "/api/x", files={"file": ("d.csv", b"a,b\n1,2", "text/csv")}
    )
    assert seen["content_type"].startswith("multipart/form-data")
    assert b"a,b" in seen["body"]
    assert out == {"uploaded": True}


def test_post_4xx_raises_nyquist_error_with_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "invalid payload"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).post("/api/x", json={"a": 1})
    assert exc.value.status_code == 422
    assert exc.value.detail == "invalid payload"


def test_get_4xx_raises_nyquist_error_with_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).get("/api/x")
    assert exc.value.status_code == 404
    assert exc.value.detail == "not found"
