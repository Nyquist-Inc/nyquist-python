"""Nyquist MCP server — the agent research desk and governed quant tools over stdio.

A local process a desktop client (Claude, Cursor, any MCP host) starts and
talks to on stdin/stdout. Every tool calls the Nyquist API through the
``nyquist`` SDK with the USER's own key, so it reads exactly what that key may
read — nothing runs under a service identity.

Two kinds of tools:

* a handful for the everyday loop of a small fund — quote, daily history,
  VaR on a basket, a grounded question to the ontology, and the bull/bear
  debate on one ticker;
* three that open the rest of the platform: search the governed surface
  (hundreds of read-or-compute endpoints), describe one tool, call it. The
  surface is discovered by search, never listed wholesale into a prompt.

Honesty rules the tools follow: a refusal from the platform reaches the model
as a tool error carrying the platform's reason; an empty answer is returned
empty; nothing is estimated on this side.

Differs on purpose from the hosted streamable-http node Nyquist runs for a
deployment behind a node key: this one ships to PyPI and runs next to the
user's client.
"""
from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import os
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal, TypeVar

import anyio.from_thread
import anyio.to_thread
import httpx
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from nyquist import Nyquist, NyquistError
from nyquist.cli import DEFAULT_CONFIG, resolve_settings
from nyquist.client import DEFAULT_BASE_URL
from nyquist.desk import Turn
from pydantic import Field

from . import __version__

T = TypeVar("T")

INSTRUCTIONS = (
    "Nyquist is an agent research desk for funds. Every tool here calls the Nyquist "
    "platform with the user's own API key and returns what the platform computed; "
    "none of them estimates. When no dedicated tool fits, search the governed surface "
    "with nyquist_search_tools, read the schema with nyquist_describe_tool, then run it "
    "with nyquist_call_tool. nyquist_bull_bear_debate takes minutes: each turn is a "
    "model call. When a tool reports missing data or a refusal, say so to the user "
    "instead of filling the gap."
)

#: Every tool reads or computes; none writes. They reach a remote platform.
READ_ONLY = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True
)
#: Same, but two runs of a model debate do not return the same text.
READ_ONLY_VARYING = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=False, open_world_hint=True
)
#: nyquist_call_tool runs whatever governed tool it is named. The surface is
#: admitted by a policy, not proven read-only tool by tool, so this tool makes
#: no read-only claim and a host may ask the user before each call.
RUNS_NAMED_TOOL = ToolAnnotations(
    read_only_hint=False, idempotent_hint=False, open_world_hint=True
)

_MISSING_KEY = (
    "no Nyquist API key: set NYQUIST_API_KEY in this MCP server's environment "
    "(nyquist.pro/settings/api) or run `nyq login` once"
)


class _DebateCancelled(Exception):
    """Raised inside the worker thread to leave a debate the client cancelled."""


class _Session:
    """One SDK client per server process, created on the first tool call.

    Lazy on purpose: a client lists tools before any key is configured, and a
    missing key should surface as a tool error that says what to set, not as a
    server that fails to start.
    """

    def __init__(self, base_url: str, api_key: str | None, transport: httpx.BaseTransport | None):
        self._base_url = base_url
        self._api_key = api_key
        self._transport = transport
        self._client: Nyquist | None = None
        self._lock = threading.Lock()

    def _nq(self) -> Nyquist:
        with self._lock:
            if self._client is None:
                if not self._api_key:
                    raise ToolError(_MISSING_KEY)
                self._client = Nyquist(
                    api_key=self._api_key, base_url=self._base_url, transport=self._transport
                )
            return self._client

    def call(self, what: str, fn: Callable[[Nyquist], T]) -> T:
        try:
            return fn(self._nq())
        except NyquistError as exc:
            status = f" (HTTP {exc.status_code})" if exc.status_code else ""
            raise ToolError(f"{what}: {exc.detail}{status}") from None


def _records(frame) -> list[dict[str, Any]]:
    """DataFrame → JSON-safe rows (dates as ISO strings, NaN as null)."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def build_server(
    *,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> MCPServer:
    session = _Session(base_url, api_key, transport)
    server = MCPServer(
        name="nyquist",
        title="Nyquist",
        description="The agent research desk for funds under $500M AUM, as MCP tools.",
        version=__version__,
        website_url="https://getnyquist.com",
        instructions=INSTRUCTIONS,
    )

    @server.tool(name="nyquist_quote", annotations=READ_ONLY)
    def quote(ticker: Annotated[str, Field(description="Equity ticker, e.g. NVDA")]) -> dict[str, Any]:
        """Latest quote and fundamentals for one equity."""
        return session.call("quote", lambda nq: nq.marketdata.price(ticker))

    @server.tool(name="nyquist_price_history", annotations=READ_ONLY)
    def price_history(
        ticker: Annotated[str, Field(description="Equity ticker, e.g. NVDA")],
        days: Annotated[int, Field(ge=1, le=1825, description="Calendar days back from today")] = 90,
    ) -> dict[str, Any]:
        """Daily OHLCV bars from the reconciled market-data store. An empty `bars` means the
        store has nothing for that symbol and window — not a zero price."""
        frame = session.call("price history", lambda nq: nq.marketdata.history(ticker, days=days))
        bars = _records(frame.reset_index()) if not frame.empty else []
        return {
            "ticker": frame.attrs.get("ticker", ticker.upper()),
            "source": frame.attrs.get("source"),
            "n_bars": len(bars),
            "bars": bars,
        }

    @server.tool(name="nyquist_value_at_risk", annotations=READ_ONLY)
    def value_at_risk(
        symbols: Annotated[list[str], Field(min_length=1, description="Tickers in the basket")],
        weights: Annotated[
            list[float] | None, Field(description="Portfolio weights, same order as symbols")
        ] = None,
        confidence: Annotated[float, Field(gt=0.5, lt=1.0)] = 0.95,
        horizon_days: Annotated[int, Field(ge=1, le=252)] = 1,
        lookback_days: Annotated[int, Field(ge=30, le=3650, description="Return window")] = 365,
        method: Literal["parametric", "historical", "monte_carlo"] = "historical",
        portfolio_value: Annotated[float, Field(gt=0, description="NAV the VaR is scaled to")] = 1.0,
    ) -> dict[str, Any]:
        """VaR and CVaR of a basket, on returns the platform fetches itself. With the default
        portfolio_value of 1.0 the figures are fractions of NAV. Losses follow the platform's
        sign convention as returned."""
        end = datetime.now(UTC).date()
        start = end - timedelta(days=lookback_days)
        return session.call(
            "value at risk",
            lambda nq: nq.risk.symbol_var(
                symbols, start.isoformat(), end.isoformat(), weights=weights, method=method,
                confidence=confidence, horizon=horizon_days, portfolio_value=portfolio_value,
            ),
        )

    @server.tool(name="nyquist_ask", annotations=READ_ONLY_VARYING)
    def ask(
        question: Annotated[str, Field(min_length=3, description="A question about your book")],
        language: Literal["en", "ru"] = "en",
    ) -> dict[str, Any]:
        """Ask a question answered from the objects in your Nyquist workspace (positions,
        risk reports, counterparties). Returns the answer and up to 20 supporting objects;
        `error` is set when the platform could not answer."""
        result = session.call("ask", lambda nq: nq.ontology.ask(question, language=language))
        return {
            "answer": result.answer,
            "intent": result.intent,
            "n_results": result.n_results,
            "error": result.error,
            "supporting_objects": _records(result.rows.head(20)) if not result.rows.empty else [],
        }

    @server.tool(name="nyquist_bull_bear_debate", annotations=READ_ONLY_VARYING)
    async def bull_bear_debate(
        ticker: Annotated[str, Field(description="Ticker or instrument to argue about")],
        ctx: Context,
        rounds: Annotated[int, Field(ge=1, le=5)] = 2,
        language: Literal["en", "ru"] = "en",
    ) -> dict[str, Any]:
        """One agent argues the bull case, one the bear case, for `rounds` rounds, then a judge
        rules. Takes minutes. `complete` is false when there is no ruling: `ended` true means
        the judge returned nothing, false means the stream stopped early. A turn with `error`
        set had no argument. Report all of it to the user as it is."""
        total = rounds * 2 + 1
        landed = itertools.count(1)
        cancelled = threading.Event()

        def on_turn(turn: Turn) -> None:
            if cancelled.is_set():
                # Leaving the stream closes the HTTP response, so an abandoned
                # debate stops spending model calls at the next turn.
                raise _DebateCancelled
            # Progress is advisory; a client that stopped listening must not
            # cost the user the debate.
            with contextlib.suppress(Exception):
                anyio.from_thread.run(ctx.report_progress, next(landed), total, f"{turn.side} done")

        try:
            debate = await anyio.to_thread.run_sync(
                lambda: session.call(
                    "bull/bear debate",
                    lambda nq: nq.desk.debate(
                        ticker.upper(), rounds=rounds, language=language, on_turn=on_turn
                    ),
                ),
                abandon_on_cancel=True,
            )
        except anyio.get_cancelled_exc_class():
            cancelled.set()
            raise
        return debate.as_dict()

    @server.tool(name="nyquist_search_tools", annotations=READ_ONLY)
    def search_tools(
        query: Annotated[str, Field(min_length=2, description="Words describing the computation")],
        limit: Annotated[int, Field(ge=1, le=50)] = 10,
    ) -> dict[str, Any]:
        """Search the governed tool surface: hundreds of read-or-compute platform endpoints
        (pricing, risk, stress, curves, portfolio analytics). Returns tool ids to pass to
        nyquist_describe_tool and nyquist_call_tool."""
        found = session.call("search tools", lambda nq: nq.tools.search(query, limit=limit))
        if not found.enabled:
            return {
                "enabled": False,
                "results": [],
                "message": "the governed tool surface is switched off on this deployment; "
                           "nothing is exposed, so an empty list is not 'no match'",
            }
        keep = ("tool_id", "method", "path", "description", "requires")
        return {
            "enabled": True,
            "total_available": found.total_available,
            "results": [{k: t.get(k) for k in keep} for t in found],
        }

    @server.tool(name="nyquist_describe_tool", annotations=READ_ONLY)
    def describe_tool(
        tool_id: Annotated[str, Field(description="An id from nyquist_search_tools")],
    ) -> dict[str, Any]:
        """The parameter schema of one governed tool — read it before nyquist_call_tool."""
        return session.call("describe tool", lambda nq: nq.tools.get(tool_id))

    @server.tool(name="nyquist_call_tool", annotations=RUNS_NAMED_TOOL)
    def call_tool(
        tool_id: Annotated[str, Field(description="An id from nyquist_search_tools")],
        parameters: Annotated[
            dict[str, Any] | None, Field(description="Arguments matching the tool's schema")
        ] = None,
    ) -> dict[str, Any]:
        """Run one governed tool as the user and return its result verbatim."""
        result = session.call(f"call {tool_id}", lambda nq: nq.tools.execute(tool_id, parameters or {}))
        return {"tool_id": tool_id, "result": result}

    return server


def serve(*, base_url: str = DEFAULT_BASE_URL, api_key: str | None = None) -> None:
    """Run the server on stdio until the client disconnects."""
    build_server(base_url=base_url, api_key=api_key).run("stdio")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="nyquist-mcp", description="Nyquist MCP server (stdio)."
    )
    parser.add_argument("--version", action="version", version=f"nyquist-mcp {__version__}")
    parser.add_argument("--base-url", help="API base URL (env NYQUIST_BASE_URL)")
    parser.add_argument("--api-key", help="personal API key (env NYQUIST_API_KEY)")
    args = parser.parse_args(argv)
    # Same precedence and the same file as `nyq`: flags, env, ~/.nyquist/config.json.
    settings = resolve_settings(args, os.environ, DEFAULT_CONFIG)
    serve(base_url=settings.base_url, api_key=settings.api_key)


__all__ = ["INSTRUCTIONS", "build_server", "main", "serve"]
