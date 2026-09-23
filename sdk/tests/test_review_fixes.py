"""Defects found in review before the first release — each test fails on the old code.

* SSE split on U+2028 and lost the turn;
* a malformed key reached httpx, whose error text quotes the header value;
* an HTML 200 parsed as "no events" and read as a judge that declined;
* ``nyq login`` re-verified the stored key instead of asking for a new one;
* the config was written in place, following a symlink;
* the persona key showed in ``repr(Turn)``.
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

from nyquist import Nyquist, NyquistError, cli
from nyquist._sse import iter_lines, parse_sse
from nyquist.client import _transport_error, checked_base_url
from nyquist.desk import Turn

from .conftest import make_client

_SSE = {"content-type": "text/event-stream"}


def _run(argv, handler, env, config_path):
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, transport=httpx.MockTransport(handler), env=env,
                    stdout=out, stderr=err, config_path=config_path)
    return code, out.getvalue(), err.getvalue()


# ── SSE line splitting ───────────────────────────────────────────────────────


def test_line_separator_inside_json_does_not_split_the_frame():
    data = json.dumps({"side": "bull", "text": "up\u2028and away\u0085"}, ensure_ascii=False)
    frames = list(parse_sse(iter_lines([f"event: agent_done\ndata: {data}\n\n"])))
    assert frames == [("agent_done", {"side": "bull", "text": "up\u2028and away\u0085"})]


def test_crlf_cut_by_a_chunk_boundary_is_one_terminator():
    chunks = ["event: a\r", "\ndata: {}\r", "\n\r", "\n"]
    assert list(parse_sse(iter_lines(chunks))) == [("a", {})]


def test_bare_cr_terminates_lines():
    assert list(iter_lines(["a\rb\r", "c"])) == ["a", "b", "c"]


def test_debate_keeps_a_turn_whose_text_holds_u2028():
    text = "margins\u2028compress"
    turn = json.dumps({"side": "bull", "round": 1, "text": text}, ensure_ascii=False)
    body = (
        f"event: agent_done\ndata: {turn}\n\n"
        f"event: debate_done\ndata: {json.dumps({'verdict': 'hold'})}\n\n"
    )
    nq = make_client(lambda r: httpx.Response(200, headers=_SSE, content=body.encode()))
    debate = nq.desk.debate("NVDA", rounds=1)
    assert [t.text for t in debate.turns] == [text]
    assert debate.complete and debate.ended


# ── stream shape ─────────────────────────────────────────────────────────────


def test_a_200_that_is_not_an_event_stream_is_an_error_not_an_empty_debate():
    nq = make_client(lambda r: httpx.Response(200, headers={"content-type": "text/html"},
                                              content=b"<html>app</html>"))
    with pytest.raises(NyquistError) as exc:
        nq.desk.debate("NVDA")
    assert "not an event stream" in exc.value.detail


def test_a_cut_stream_is_told_apart_from_a_judge_that_declined(tmp_path):
    cut = "event: agent_done\ndata: {\"side\": \"bull\", \"round\": 1, \"text\": \"up\"}\n\n"
    declined = cut + (
        'event: agent_done\ndata: {"side": "judge", "text": "", "error": "budget exhausted"}\n\n'
        'event: debate_done\ndata: {"verdict": ""}\n\n'
    )
    env = {"NYQUIST_API_KEY": "nyquist_k", "NYQUIST_BASE_URL": "https://api.test"}
    cfg = tmp_path / "none.json"

    code, _, err = _run(["desk", "NVDA", "--rounds", "1"],
                        lambda r: httpx.Response(200, headers=_SSE, content=cut.encode()), env, cfg)
    assert code == 1 and "stream ended before the debate closed (1 turns received)" in err

    code, _, err = _run(["desk", "NVDA", "--rounds", "1"],
                        lambda r: httpx.Response(200, headers=_SSE, content=declined.encode()),
                        env, cfg)
    assert code == 1 and "judge returned no ruling: budget exhausted" in err


# ── the key never appears in an error ────────────────────────────────────────


def test_trailing_newline_is_stripped_from_the_key():
    seen = {}

    def handler(request):
        seen["key"] = request.headers["x-api-key"]
        return httpx.Response(200, json={})

    Nyquist(api_key="nyquist_abc\n", base_url="https://api.test",
            transport=httpx.MockTransport(handler))._request("GET", "/x")
    assert seen["key"] == "nyquist_abc"


@pytest.mark.parametrize("bad", ["nyquist_a\nb", "nyquist a", "nyquist_é", "nyquist_\x00"])
def test_a_malformed_key_is_refused_without_quoting_it(bad):
    with pytest.raises(NyquistError) as exc:
        Nyquist(api_key=bad, base_url="https://api.test")
    assert bad.strip() not in str(exc.value)


def test_a_protocol_error_is_reported_by_class_not_by_text():
    exc = httpx.LocalProtocolError("Illegal header value b'nyquist_SECRET\\n'")
    error = _transport_error("request to /x", exc)
    assert "SECRET" not in error.detail
    assert "LocalProtocolError" in error.detail


# ── plain http ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("url", ["https://api.nyquist.pro", "http://localhost:8000",
                                 "http://127.0.0.1:8000", "http://[::1]:8000",
                                 "http://gateway:8000", "http://10.0.0.5"])
def test_base_urls_that_keep_the_key_off_the_open_network(url):
    assert checked_base_url(url + "/") == url


@pytest.mark.parametrize("url", ["http://api.nyquist.pro", "http://8.8.8.8"])
def test_plain_http_to_a_routable_host_is_refused(url):
    with pytest.raises(NyquistError, match="plain http"):
        checked_base_url(url)


# ── login ────────────────────────────────────────────────────────────────────


def test_login_does_not_reverify_the_stored_key_it_is_meant_to_replace(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"api_key": "nyquist_revoked"}))

    def never(request):
        raise AssertionError("the stored key must not be sent")

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    code, _, err = _run(["login"], never, {}, config)
    assert code == 2 and "no terminal to prompt on" in err
    assert json.loads(config.read_text())["api_key"] == "nyquist_revoked"


def test_login_takes_the_key_from_the_environment(tmp_path):
    config = tmp_path / "config.json"
    code, _, _ = _run(["login"], lambda r: httpx.Response(200, json={"enabled": True}),
                      {"NYQUIST_API_KEY": "nyquist_env"}, config)
    assert code == 0 and json.loads(config.read_text())["api_key"] == "nyquist_env"


def test_login_replaces_a_symlink_instead_of_writing_through_it(tmp_path):
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}")
    config = tmp_path / "config.json"
    config.symlink_to(elsewhere)

    code, _, _ = _run(["--api-key", "nyquist_k", "login", "--no-verify"],
                      lambda r: httpx.Response(500), {}, config)
    assert code == 0
    assert not config.is_symlink()
    assert elsewhere.read_text() == "{}"
    assert oct(config.stat().st_mode & 0o777) == oct(0o600)
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".config-")] == []


def test_login_no_verify_still_refuses_a_key_it_could_never_use(tmp_path):
    config = tmp_path / "config.json"
    code, _, err = _run(["--api-key", "nyquist a", "login", "--no-verify"],
                        lambda r: httpx.Response(500), {}, config)
    assert code == 2 and "whitespace" in err
    assert not config.exists()


# ── persona key out of the repr ──────────────────────────────────────────────


def test_turn_repr_hides_the_persona_key():
    turn = Turn(side="bull", text="up", round=1, agent_id="persona_key")
    assert "persona_key" not in repr(turn)
    assert turn.agent_id == "persona_key"


def test_no_stray_temp_files_after_a_failed_write(tmp_path, monkeypatch):
    config = tmp_path / "config.json"

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        cli._write_config(config, "https://api.test", "nyquist_k")
    assert list(Path(tmp_path).iterdir()) == []
