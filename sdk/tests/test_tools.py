"""``nq.tools`` — the governed tool surface (``/api/ontology/tools/*``)."""
from __future__ import annotations

import json

import httpx
import pytest

from nyquist import NyquistError

from .conftest import make_client

_TOOL = {
    "tool_id": "api.zcyc.get",
    "path": "/api/zcyc/",
    "method": "GET",
    "description": "Zero-coupon yield curve",
    "parameters_schema": {"type": "object", "properties": {}},
    "requires": "none",
    "reason": "read",
}


def test_search_sends_query_and_limit_and_keeps_the_enabled_flag():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        seen["key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json={"query": "yield", "results": [_TOOL],
                                         "total_available": 1400, "enabled": True})

    found = make_client(handler).tools.search("yield", limit=5)
    assert seen == {"path": "/api/ontology/tools/search", "params": {"q": "yield", "limit": "5"},
                    "key": "nyquist_test-key"}
    assert found.enabled is True
    assert found.total_available == 1400
    assert [t["tool_id"] for t in found] == ["api.zcyc.get"]
    assert len(found) == 1


def test_search_on_a_disabled_surface_is_empty_and_says_so():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": "x", "results": [], "total_available": 0,
                                         "enabled": False})

    found = make_client(handler).tools.search("x")
    assert found.enabled is False
    assert list(found) == []
    assert "MANIFEST_TOOLS_ENABLED" in str(found)


def test_get_returns_the_tool_view():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/ontology/tools/api.zcyc.get"
        return httpx.Response(200, json=_TOOL)

    assert make_client(handler).tools.get("api.zcyc.get")["path"] == "/api/zcyc/"


def test_get_unknown_tool_raises_with_the_backend_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Tool 'x' is not in the governed surface"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).tools.get("x")
    assert exc.value.status_code == 404
    assert "governed surface" in exc.value.detail


def test_execute_posts_parameters_and_unwraps_the_result():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"tool_id": "api.risk.portfolio.var.post",
                                         "result": {"var": -1.2}})

    out = make_client(handler).tools.execute("api.risk.portfolio.var.post", {"confidence": 0.99})
    assert seen == {"path": "/api/ontology/tools/api.risk.portfolio.var.post/execute",
                    "body": {"parameters": {"confidence": 0.99}}}
    assert out == {"var": -1.2}


def test_execute_without_params_sends_an_empty_mapping():
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {"parameters": {}}
        return httpx.Response(200, json={"tool_id": "api.zcyc.get", "result": []})

    assert make_client(handler).tools.execute("api.zcyc.get") == []


def test_execute_refusal_is_an_error_not_a_result():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "api.x → 403: insufficient clearance"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler).tools.execute("api.x", {})
    assert exc.value.status_code == 400
    assert "insufficient clearance" in exc.value.detail


def test_governance_is_passed_through():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/ontology/tools/governance"
        return httpx.Response(200, json={"enabled": True, "total_tools": 3,
                                         "by_permission": {"none": 3}, "by_method": {"GET": 3}})

    assert make_client(handler).tools.governance()["total_tools"] == 3
