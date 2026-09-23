"""Core client tests: auth header injection, error mapping, env-key default."""
from __future__ import annotations

import httpx
import pytest

from nyquist import Nyquist, NyquistError

from .conftest import make_client


def test_injects_x_api_key_header():
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers.get("x-api-key")
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"status": "ok", "service": "market_data"})

    nq = make_client(handler)
    nq._request("GET", "/api/market-data/health")
    assert seen["key"] == "nyquist_test-key"
    assert seen["auth"] is None  # B2B key path, not a Bearer token


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("NYQUIST_API_KEY", raising=False)
    with pytest.raises(NyquistError) as exc:
        Nyquist()
    assert exc.value.status_code is None
    assert "NYQUIST_API_KEY" in exc.value.detail


def test_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("NYQUIST_API_KEY", "nyquist_env-key")
    nq = Nyquist(base_url="https://api.test", transport=httpx.MockTransport(
        lambda r: httpx.Response(200, json={})
    ))
    assert nq.api_key == "nyquist_env-key"


def test_non_2xx_raises_with_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "ontology object not found"})

    with pytest.raises(NyquistError) as exc:
        make_client(handler)._request("GET", "/api/x")
    assert exc.value.status_code == 404
    assert exc.value.detail == "ontology object not found"


def test_context_manager_closes():
    nq = make_client(lambda r: httpx.Response(200, json={}))
    with nq as client:
        assert client is nq
    assert nq._client.is_closed
