"""Stress sub-client — wraps ``/api/stress/*`` (async-job contract).

Also hosts :func:`_poll_job`, the shared submit→poll helper reused by
:class:`~nyquist.backtest.Backtest` (one polling implementation, not two).
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from .errors import NyquistError

if TYPE_CHECKING:
    from .client import Nyquist


class Stress:
    """Portfolio stress-testing over the async-job contract (202
    ``{job_id}`` → poll ``GET /job/{id}``). Reachable with an API key.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def submit(self, payload: dict[str, Any]) -> str:
        """Enqueue a stress job, returning its ``job_id``.

        Wraps ``POST /api/stress/submit`` (202 ``{job_id, status}``).
        ``payload`` is the raw submit body, e.g.
        ``{"portfolio": {...}, "scenario": "rates_up_200bp"}``.
        """
        data = self._nq._request("POST", "/api/stress/submit", json_body=payload)
        return data["job_id"]

    def job(self, job_id: str) -> dict[str, Any]:
        """Fetch the current HASH state for ``job_id``.

        Wraps ``GET /api/stress/job/{id}`` — ``status`` is one of
        ``enqueued``/``running``/``completed``/``failed``; 404 once the
        24h TTL elapses.
        """
        return self._nq._request("GET", f"/api/stress/job/{job_id}")

    def run(
        self,
        payload: dict[str, Any],
        *,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Submit and block until the job reaches a terminal state.

        Convenience over :meth:`submit` + :meth:`job`: polls every
        ``poll_interval`` seconds up to ``timeout`` and returns the job's
        ``result``. Raises :class:`~nyquist.errors.NyquistError` if the job
        fails or the timeout elapses first.
        """
        job_id = self.submit(payload)
        return _poll_job(
            self._nq,
            f"/api/stress/job/{job_id}",
            poll_interval=poll_interval,
            timeout=timeout,
        )

    def scenarios(self) -> Any:
        """List available historical crisis scenarios.

        Wraps ``GET /api/stress/historical-scenarios``.
        """
        return self._nq._request("GET", "/api/stress/historical-scenarios")


def _poll_job(
    nq: Nyquist,
    job_path: str,
    *,
    poll_interval: float = 2.0,
    timeout: float = 300.0,
) -> dict[str, Any]:
    """Poll ``GET {job_path}`` until ``status`` is terminal or ``timeout`` elapses.

    Shared by :meth:`Stress.run` and ``Backtest.run_async`` — the async-job
    contract is identical across worker domains. Returns the job's
    ``result`` on ``completed``; raises :class:`NyquistError` on ``failed``
    (carrying the job's ``error``) or on timeout.
    """
    deadline = time.monotonic() + timeout
    while True:
        status = nq._request("GET", job_path)
        state = status.get("status")
        if state == "completed":
            return status.get("result")
        if state == "failed":
            raise NyquistError(
                None, f"job failed: {status.get('error', 'unknown error')}"
            )
        if time.monotonic() >= deadline:
            raise NyquistError(
                None,
                f"job did not complete within {timeout}s "
                f"(last status: {state!r})",
            )
        time.sleep(poll_interval)


__all__ = ["Stress"]
