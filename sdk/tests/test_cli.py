"""``nyq`` — the console entry point (stdlib + httpx, hermetic MockTransport)."""
from __future__ import annotations

import io
import json
from pathlib import Path

import httpx
import pytest

from nyquist import cli

_TOOL = {"tool_id": "api.zcyc.get", "path": "/api/zcyc/", "method": "GET",
         "description": "Zero-coupon yield curve", "parameters_schema": {"type": "object"},
         "requires": "none", "reason": "read"}


_NO_CONFIG = Path("/nonexistent/nyquist/config.json")


def _run(argv, handler, env=None):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, transport=httpx.MockTransport(handler), env=env or {},
                    stdout=out, stderr=err, config_path=_NO_CONFIG)
    return code, out.getvalue(), err.getvalue()


_ENV = {"NYQUIST_API_KEY": "nyquist_k", "NYQUIST_BASE_URL": "https://api.test"}


def test_tools_search_prints_one_line_per_tool():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/ontology/tools/search"
        assert request.url.params["q"] == "yield curve"
        return httpx.Response(200, json={"query": "yield curve", "results": [_TOOL],
                                         "total_available": 1, "enabled": True})

    code, out, _ = _run(["tools", "search", "yield", "curve"], handler, _ENV)
    assert code == 0
    assert "api.zcyc.get" in out
    assert "GET /api/zcyc/" in out


def test_tools_search_on_disabled_surface_names_the_flag_and_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": "x", "results": [], "total_available": 0,
                                         "enabled": False})

    code, out, err = _run(["tools", "search", "x"], handler, _ENV)
    assert code == 1
    assert "MANIFEST_TOOLS_ENABLED" in err


def test_tools_call_with_inline_json_prints_the_result():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json={"tool_id": "api.risk.portfolio.var.post",
                                         "result": {"var": -1.2}})

    code, out, _ = _run(["tools", "call", "api.risk.portfolio.var.post", "--json",
                         '{"confidence": 0.99}'], handler, _ENV)
    assert code == 0
    assert seen == {"body": {"parameters": {"confidence": 0.99}}, "key": "nyquist_k"}
    assert json.loads(out) == {"var": -1.2}


def test_tools_call_with_file(tmp_path):
    params = tmp_path / "p.json"
    params.write_text('{"a": 1}')

    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {"parameters": {"a": 1}}
        return httpx.Response(200, json={"tool_id": "t", "result": "ok"})

    code, out, _ = _run(["tools", "call", "t", "--file", str(params)], handler, _ENV)
    assert code == 0
    assert json.loads(out) == "ok"


def test_tools_call_refusal_is_exit_1_with_the_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "tool 't' is not in the governed surface"})

    code, _, err = _run(["tools", "call", "t"], handler, _ENV)
    assert code == 1
    assert "governed surface" in err


def test_tools_call_rejects_invalid_json_before_any_request():
    called = []

    def handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        return httpx.Response(200, json={})

    code, _, err = _run(["tools", "call", "t", "--json", "{not json"], handler, _ENV)
    assert code == 2
    assert called == []
    assert "JSON" in err


def test_missing_key_is_a_config_error():
    code, _, err = _run(["tools", "search", "x"], lambda r: httpx.Response(200, json={}), {})
    assert code == 2
    assert "NYQUIST_API_KEY" in err


def test_flags_override_env(monkeypatch):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["host"] = request.url.host
        seen["key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json={"query": "x", "results": [], "total_available": 0,
                                         "enabled": True})

    _run(["--base-url", "https://flag.test", "--api-key", "flagkey", "tools", "search", "x"],
         handler, _ENV)
    assert seen == {"host": "flag.test", "key": "flagkey"}


# ── doctor ───────────────────────────────────────────────────────────────────


def _doctor_handler(*, health=200, governance=None, readiness=None):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/health":
            return httpx.Response(health, json={"status": "ok", "build": "abc123"})
        if path == "/api/ontology/tools/governance":
            default_gov = {"enabled": True, "total_tools": 12, "by_permission": {},
                           "by_method": {}}
            return httpx.Response(200, json=governance if governance is not None else default_gov)
        if path == "/api/agents/readiness":
            default_rd = {"ready": True, "flag_enabled": True, "mock_mode": False,
                          "aliases": [], "blockers": []}
            return httpx.Response(200, json=readiness if readiness is not None else default_rd)
        return httpx.Response(404, json={"detail": "no such route"})
    return handler


def test_doctor_all_ok_exits_zero():
    code, out, _ = _run(["doctor"], _doctor_handler(), _ENV)
    assert code == 0
    statuses = [ln.split()[0] for ln in out.splitlines() if ln.strip()]
    assert all(s == "ok" for s in statuses if s in ("ok", "fail", "skipped")), out
    assert "health" in out and "tools" in out and "agents" in out


def test_doctor_names_the_flag_when_the_surface_is_off():
    gov = {"enabled": False, "total_tools": 0, "by_permission": {}, "by_method": {}}
    code, out, _ = _run(["doctor"], _doctor_handler(governance=gov), _ENV)
    assert code == 1
    assert "MANIFEST_TOOLS_ENABLED" in out
    assert "fail" in out


def test_doctor_reports_agents_not_ready_with_the_blockers():
    rd = {"ready": False, "flag_enabled": False, "mock_mode": False, "aliases": [],
          "blockers": ["AGENTS_ENABLED is off"]}
    code, out, _ = _run(["doctor"], _doctor_handler(readiness=rd), _ENV)
    assert code == 1
    assert "AGENTS_ENABLED is off" in out


def test_doctor_without_a_key_skips_authenticated_checks_with_a_reason():
    code, out, _ = _run(["doctor"], _doctor_handler(), {"NYQUIST_BASE_URL": "https://api.test"})
    assert code == 3
    assert out.count("skipped") == 2
    assert "NYQUIST_API_KEY" in out


def test_doctor_unreachable_gateway_is_a_fail_not_a_traceback():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    code, out, _ = _run(["doctor"], handler, _ENV)
    assert code == 1
    assert out.count("fail") >= 1
    assert "Traceback" not in out


@pytest.mark.parametrize("argv", [[], ["tools"]])
def test_no_command_prints_usage(argv):
    code, _, err = _run(argv, lambda r: httpx.Response(200, json={}), _ENV)
    assert code == 2
