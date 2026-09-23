"""The :class:`Nyquist` client — a thin, synchronous httpx wrapper.

Design:
  - One ``httpx.Client`` per ``Nyquist`` instance (reused across calls); use as
    a context manager so it closes cleanly.
  - Auth is an **API key** sent on every request as the ``X-API-Key`` header.
    The key is taken from the explicit ``api_key=`` argument or the ``NYQUIST_API_KEY`` env.
  - Every non-2xx response raises :class:`NyquistError` carrying status + detail.
  - Tabular endpoints are shaped into pandas DataFrames by the sub-clients.

The client is synchronous on purpose: notebook research reads as
``nq.marketdata.history("NVDA")`` returning a DataFrame, not a coroutine.
"""
from __future__ import annotations

import ipaddress
import os
from collections.abc import Iterator
from typing import Any

import httpx

from . import plot as _plot
from ._sse import Event, iter_lines, parse_sse
from .agents import Agents
from .backtest import Backtest
from .crypto import Crypto
from .datasets import Datasets
from .desk import Desk
from .errors import NyquistError
from .ledger import ExecutionLedger
from .macro import Macro
from .marketdata import MarketData
from .ontology import Ontology
from .portfolio import Portfolio
from .reports import Reports
from .risk import Risk
from .stress import Stress
from .tools import Tools

DEFAULT_BASE_URL = "https://api.nyquist.pro"
API_KEY_HEADER = "X-API-Key"
#: A streamed agent turn is one model call; the gap between two events is
#: bounded by the slowest turn, not by the whole debate.
STREAM_TIMEOUT = httpx.Timeout(30.0, read=300.0)


class Nyquist:
    """Entry point to the Nyquist quant-research API.

    Example::

        from nyquist import Nyquist

        nq = Nyquist()                 # reads NYQUIST_API_KEY from the env
        df = nq.marketdata.history("NVDA", days=365)
        var = nq.risk.var(df["close"].pct_change().dropna().tolist())
        ans = nq.ontology.ask("What is our largest counterparty exposure?")
        print(ans.answer)
        hits = nq.tools.search("yield curve")          # governed tool surface
        curve = nq.tools.execute(hits.results[0]["tool_id"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        key = clean_api_key(api_key if api_key is not None else os.getenv("NYQUIST_API_KEY"))
        self.api_key = key
        self.base_url = checked_base_url(base_url)
        if client is not None:
            self._client = client
        else:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={API_KEY_HEADER: key, "Accept": "application/json"},
                timeout=timeout,
                transport=transport,
            )

        # Sub-namespaces.
        self.marketdata = MarketData(self)
        self.risk = Risk(self)
        self.portfolio = Portfolio(self)
        self.ontology = Ontology(self)
        self.stress = Stress(self)
        self.backtest = Backtest(self)
        self.macro = Macro(self)
        self.crypto = Crypto(self)
        self.agents = Agents(self)
        self.desk = Desk(self)
        self.ledger = ExecutionLedger(self)
        self.datasets = Datasets(self)
        self.reports = Reports(self)
        self.tools = Tools(self)
        # Optional matplotlib helpers; matplotlib is imported lazily inside the
        # helpers so the SDK works fine without the [plot] extra installed.
        self.plot = _plot

    # -- lifecycle -----------------------------------------------------------

    def __enter__(self) -> Nyquist:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # -- generic escape-hatch -------------------------------------------------
    #
    # Hundreds of endpoints accept the API key; only a handful get a
    # dedicated sub-client below. ``get``/``post`` reach any of them directly.

    def get(self, path: str, **params: Any) -> Any:
        """Generic GET — reach any endpoint the API key can reach.

        Returns parsed JSON (or raw text for non-JSON responses); raises
        :class:`NyquistError` on any non-2xx. ``path`` is relative to
        ``base_url``.

        Example::

            nq.get("/api/execution-ledger/sources")
        """
        return self._request("GET", path, params=params or None)

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        files: Any = None,
        data: Any = None,
    ) -> Any:
        """Generic POST — reach any endpoint the API key can reach.

        Returns parsed JSON (or raw text for non-JSON responses); raises
        :class:`NyquistError` on any non-2xx. ``path`` is relative to
        ``base_url``. Pass ``files``/``data`` (no ``json``) for a multipart
        upload.

        Example::

            nq.post("/api/datasets", files={"file": ("d.csv", data, "text/csv")})
        """
        return self._request(
            "POST", path, params=params, json_body=json, files=files, data=data
        )

    # -- core request helper -------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        files: Any = None,
        data: Any = None,
    ) -> Any:
        """Issue one request, raising :class:`NyquistError` on any failure."""
        try:
            resp = self._client.request(
                method, path, params=_clean(params), json=json_body,
                files=files, data=data,
            )
        except httpx.HTTPError as exc:
            raise _transport_error(f"request to {path}", exc) from None

        if resp.status_code >= 400:
            raise NyquistError(resp.status_code, _detail(resp))

        ctype = resp.headers.get("content-type", "")
        if ctype.startswith("application/json"):
            return resp.json()
        return resp.text

    def _stream_events(self, path: str, *, json_body: Any) -> Iterator[Event]:
        """POST and yield ``(event, data)`` from a ``text/event-stream`` reply.

        A refusal (4xx/5xx) arrives before the first frame and raises
        :class:`NyquistError` with the server's ``detail``, like any request. A
        2xx that is not an event stream (an HTML fallback page behind a wrong
        base URL) raises too, instead of parsing as "no events".
        """
        try:
            with self._client.stream(
                "POST", path, json=json_body, timeout=STREAM_TIMEOUT,
                headers={"Accept": "text/event-stream"},
            ) as resp:
                if resp.status_code >= 400:
                    resp.read()
                    raise NyquistError(resp.status_code, _detail(resp))
                ctype = resp.headers.get("content-type", "")
                if not ctype.startswith("text/event-stream"):
                    raise NyquistError(
                        resp.status_code,
                        f"{path} answered {ctype or 'no content-type'}, not an event stream "
                        f"— is {self.base_url} the Nyquist API?",
                    )
                yield from parse_sse(iter_lines(resp.iter_text()))
        except httpx.HTTPError as exc:
            raise _transport_error(f"stream from {path}", exc) from None


def clean_api_key(key: str | None) -> str:
    """The key as it will travel in a header, or a refusal that does not quote it.

    A trailing newline from ``.env`` or a host config is stripped. Anything
    httpx would reject as a header value is refused HERE: httpx names the
    offending value in its error, and that text would carry the key into a
    traceback, the terminal or a model's tool result.
    """
    key = (key or "").strip()
    if not key:
        raise NyquistError(
            None,
            "No API key supplied — pass api_key=... or set the "
            "NYQUIST_API_KEY environment variable.",
        )
    if not key.isascii() or not key.isprintable() or any(c.isspace() for c in key):
        raise NyquistError(
            None,
            "The API key contains whitespace or non-printable characters — "
            "check the variable or config file for a stray character.",
        )
    return key


def checked_base_url(base_url: str) -> str:
    """Refuse plain http to a routable host: the key would cross the network in clear.

    Allowed over http: loopback, private addresses, and single-label hosts
    (``gateway`` in a compose network) — none of them leaves the machine or
    the private network.
    """
    url = base_url.rstrip("/")
    parsed = httpx.URL(url)
    if parsed.scheme != "http":
        return url
    host = parsed.host
    try:
        private = ipaddress.ip_address(host).is_private
    except ValueError:
        private = host == "localhost" or "." not in host
    if not private:
        raise NyquistError(
            None, f"refusing to send the API key over plain http to {host} — use https://"
        )
    return url


def _transport_error(what: str, exc: httpx.HTTPError) -> NyquistError:
    # A protocol error echoes the offending request bytes (a header value) —
    # name the class, never the text.
    if isinstance(exc, httpx.LocalProtocolError):
        return NyquistError(None, f"{what} failed: {type(exc).__name__}")
    return NyquistError(None, f"{what} failed: {exc}")


def _clean(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop ``None`` params so they are not serialised as literal values."""
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}


def _detail(resp: httpx.Response) -> str:
    """Extract a FastAPI ``{"detail": ...}`` message, falling back to body text."""
    try:
        body = resp.json()
    except ValueError:
        return resp.text or resp.reason_phrase
    if isinstance(body, dict) and "detail" in body:
        return str(body["detail"])
    return resp.text or resp.reason_phrase


__all__ = ["Nyquist", "checked_base_url", "clean_api_key"]
