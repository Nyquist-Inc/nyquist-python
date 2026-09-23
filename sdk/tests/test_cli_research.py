"""``nyq login`` / ``quote`` / ``history`` / ``desk`` / ``mcp`` (hermetic MockTransport)."""
from __future__ import annotations

import io
import json
import stat
import sys
from pathlib import Path

import httpx
import pytest

from nyquist import __version__, cli

_ENV = {"NYQUIST_API_KEY": "nyquist_k", "NYQUIST_BASE_URL": "https://api.test"}


def _run(argv, handler, env=None, config_path=Path("/nonexistent/nyquist/config.json")):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, transport=httpx.MockTransport(handler),
                    env=env if env is not None else _ENV,
                    stdout=out, stderr=err, config_path=config_path)
    return code, out.getvalue(), err.getvalue()


def _never(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"no request expected, got {request.url}")


def _sse(*frames: tuple[str, dict]) -> httpx.Response:
    body = "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in frames)
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body.encode())


# ── quote / history ──────────────────────────────────────────────────────────


def test_quote_prints_the_payload_as_json():
    def handler(request):
        assert request.url.path == "/api/market-data/stock/NVDA"
        return httpx.Response(200, json={"ticker": "NVDA", "price": 181.2})

    code, out, _ = _run(["quote", "NVDA"], handler)
    assert code == 0
    assert json.loads(out) == {"ticker": "NVDA", "price": 181.2}


_BARS = {"ticker": "NVDA", "source": "golden", "bars": [
    {"date": "2026-09-21", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 10},
    {"date": "2026-09-22", "open": 1.5, "high": 2.5, "low": 1, "close": 2, "volume": 12},
]}


def test_history_prints_csv_with_iso_dates():
    def handler(request):
        assert request.url.params["lookback_days"] == "30"
        return httpx.Response(200, json=_BARS)

    code, out, _ = _run(["history", "NVDA", "--days", "30"], handler)
    assert code == 0
    lines = out.strip().splitlines()
    assert lines[0].startswith("date,open,high,low,close,volume")
    assert lines[1].startswith("2026-09-21,")


def test_history_json_carries_source():
    code, out, _ = _run(["history", "NVDA", "--json"], lambda r: httpx.Response(200, json=_BARS))
    body = json.loads(out)
    assert code == 0 and body["source"] == "golden" and len(body["bars"]) == 2


def test_history_empty_is_a_failure_on_stderr_not_an_empty_csv():
    code, out, err = _run(["history", "ZZZZ"],
                          lambda r: httpx.Response(200, json={"ticker": "ZZZZ", "bars": []}))
    assert code == 1
    assert out == ""
    assert "no daily bars for ZZZZ" in err


# ── desk ─────────────────────────────────────────────────────────────────────

_DEBATE = (
    ("agent_done", {"side": "bull", "round": 1, "agent_id": "x", "text": "up", "error": None}),
    ("agent_done", {"side": "bear", "round": 1, "agent_id": "y", "text": "down", "error": None}),
    ("agent_done", {"side": "judge", "agent_id": "z", "text": "hold"}),
    ("debate_done", {"instrument": "NVDA", "verdict": "hold"}),
)


def test_desk_streams_sides_without_persona_ids():
    code, out, err = _run(["desk", "nvda", "--rounds", "1"], lambda r: _sse(*_DEBATE))
    assert code == 0
    assert "── BULL · round 1\nup" in out
    assert "── VERDICT\nhold" in out
    # Persona ids are code keys, not public labels.
    assert "x" not in out.split() and "agent_id" not in out
    assert "Bull vs bear on NVDA" in err


def test_desk_json_prints_the_whole_debate():
    code, out, _ = _run(["desk", "NVDA", "--json"], lambda r: _sse(*_DEBATE))
    body = json.loads(out)
    assert code == 0 and body["complete"] is True and body["verdict"] == "hold"


def test_desk_without_verdict_exits_1_and_says_why():
    frames = (
        ("agent_done", {"side": "bull", "round": 1, "text": "", "error": "timeout"}),
        ("debate_done", {"verdict": ""}),
    )
    code, out, err = _run(["desk", "NVDA", "--rounds", "1"], lambda r: _sse(*frames))
    assert code == 1
    assert "(no argument — timeout)" in out
    assert "no verdict" in err and "1 of 1 turns failed" in err


def test_desk_rejects_rounds_outside_the_server_range():
    code, _, _ = _run(["desk", "NVDA", "--rounds", "9"], _never)
    assert code == 2


# ── login ────────────────────────────────────────────────────────────────────


def test_login_verifies_then_writes_0600_and_keeps_other_keys(tmp_path):
    config = tmp_path / "nyq" / "config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"org": "kept", "api_key": "old"}))
    config.chmod(0o644)  # a pre-existing, too-open file must be tightened too

    def handler(request):
        assert request.url.path == "/api/ontology/tools/governance"
        assert request.headers["x-api-key"] == "nyquist_new"
        return httpx.Response(200, json={"enabled": True, "total_tools": 3})

    code, out, _ = _run(["--api-key", "nyquist_new", "login"], handler, env={}, config_path=config)
    assert code == 0
    saved = json.loads(config.read_text())
    assert saved == {"org": "kept", "api_key": "nyquist_new", "endpoint": "https://api.nyquist.pro"}
    assert stat.S_IMODE(config.stat().st_mode) == 0o600
    assert "accepted by the gateway" in out


def test_login_rejected_key_writes_nothing(tmp_path):
    config = tmp_path / "config.json"
    code, _, err = _run(["--api-key", "bad", "login"],
                        lambda r: httpx.Response(401, json={"detail": "Invalid API key"}),
                        env={}, config_path=config)
    assert code == 1
    assert "Invalid API key" in err
    assert not config.exists()


def test_login_without_key_and_without_a_terminal_is_a_usage_error(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    code, _, err = _run(["login"], _never, env={}, config_path=tmp_path / "c.json")
    assert code == 2
    assert "no terminal to prompt on" in err


def test_login_no_verify_skips_the_gateway(tmp_path):
    config = tmp_path / "c.json"
    code, out, _ = _run(["--api-key", "k", "login", "--no-verify"], _never,
                        env={}, config_path=config)
    assert code == 0 and "not verified" in out
    assert json.loads(config.read_text())["api_key"] == "k"


# ── mcp / version ────────────────────────────────────────────────────────────


def test_mcp_without_the_package_names_the_install(monkeypatch):
    monkeypatch.setitem(sys.modules, "nyquist_mcp", None)
    monkeypatch.setitem(sys.modules, "nyquist_mcp.server", None)
    code, _, err = _run(["mcp"], _never, env={})
    assert code == 2
    assert "pip install nyquist-mcp" in err


def test_version_flag(capsys):
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--version"])
    assert __version__ in capsys.readouterr().out
