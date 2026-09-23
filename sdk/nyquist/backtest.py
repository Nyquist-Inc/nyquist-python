"""Backtest sub-client — wraps ``/api/backtest/*`` (sync shim + async jobs)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .stress import _poll_job

if TYPE_CHECKING:
    from .client import Nyquist


class Backtest:
    """Portfolio backtesting — the sync ``/run`` deprecation shim plus the
    async-job contract (202 ``{job_id}`` → poll ``GET /job/{id}``).
    Reachable with an API key.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Synchronous backtest run (deprecation shim — Sunset header set
        server-side; prefer :meth:`submit` + :meth:`job`).

        Wraps ``POST /api/backtest/run``. Accepts either the legacy
        ``{mu, cov_matrix, ...}`` Monte-Carlo payload (returns the full
        result) or the newer ``{symbols, strategy, ...}`` shape (returns a
        deterministic ack).
        """
        return self._nq._request("POST", "/api/backtest/run", json_body=payload)

    def historical(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Historical backtest over caller-supplied price paths.

        Wraps ``POST /api/backtest/historical`` — ``payload`` matches
        ``HistoricalBacktestRequest`` (``historical_prices``,
        ``rebalance_frequency``, ``strategy_type``, ...).
        """
        return self._nq._request(
            "POST", "/api/backtest/historical", json_body=payload
        )

    def submit(self, payload: dict[str, Any]) -> str:
        """Enqueue an async backtest job, returning its ``job_id``.

        Wraps ``POST /api/backtest/submit`` — ``payload`` is
        ``{"kind": "portfolio_run"|"historical"|"walk_forward"|
        "symbol_historical"|"symbol_walk_forward", "params": {...}}``
        (``kind`` defaults server-side to ``symbol_historical`` when a
        terse ``{symbols, start_date, end_date, strategy}`` body is sent).
        """
        data = self._nq._request(
            "POST", "/api/backtest/submit", json_body=payload
        )
        return data["job_id"]

    def job(self, job_id: str) -> dict[str, Any]:
        """Fetch the current HASH state for ``job_id``.

        Wraps ``GET /api/backtest/job/{id}``; 404 once the 24h TTL elapses.
        """
        return self._nq._request("GET", f"/api/backtest/job/{job_id}")

    def run_async(
        self,
        payload: dict[str, Any],
        *,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Submit and block until the async job reaches a terminal state.

        Mirrors :meth:`~nyquist.stress.Stress.run` — see :meth:`submit`.
        Raises :class:`~nyquist.errors.NyquistError` on job failure or
        timeout.
        """
        job_id = self.submit(payload)
        return _poll_job(
            self._nq,
            f"/api/backtest/job/{job_id}",
            poll_interval=poll_interval,
            timeout=timeout,
        )


__all__ = ["Backtest"]
