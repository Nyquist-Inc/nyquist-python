"""Reports sub-client — wraps ``/api/reports`` write-back.

The "save/share" half of the research loop:
``nq.reports.save(...)`` persists a strategy report under the caller's
owner-scoped key; ``nq.reports.download_url(key)`` turns that key back into
a fetchable presigned URL.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Nyquist


class Reports:
    """Save, list and fetch download links for the caller's saved reports."""

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def save(
        self,
        *,
        title: str,
        returns: list[float],
        metrics: dict[str, Any],
        weights: dict[str, float] | None = None,
        benchmark_returns: list[float] | None = None,
    ) -> dict[str, Any]:
        """Generate and persist a strategy report, returning its storage key.

        Wraps ``POST /api/reports/save`` -> ``{"saved": true, "key":
        "nyquist-reports/<owner>/<year>/Q<q>/report_<ts>.html"}``. The
        returned ``key`` is bucket-prefixed and round-trips unchanged into
        :meth:`download_url`.
        """
        body = {
            "title": title,
            "returns": list(returns),
            "metrics": metrics,
            "weights": weights,
            "benchmark_returns": benchmark_returns,
        }
        return self._nq._request("POST", "/api/reports/save", json_body=body)

    def list(self) -> list[dict[str, Any]]:
        """The caller's own saved reports (owner-scoped).

        Wraps ``GET /api/reports/list`` -> ``{"reports": [{"key", "size",
        "last_modified"}, ...]}``; this method unwraps the envelope and
        returns the list directly.
        """
        out = self._nq._request("GET", "/api/reports/list")
        return out.get("reports", [])

    def download_url(self, key: str) -> str:
        """Turn a saved report ``key`` into a short-lived presigned URL.

        Wraps ``GET /api/reports/download?key=...`` -> ``{"url": "..."}``
        (1h expiry). ``key`` must be the exact bucket-prefixed string
        returned by :meth:`save` or :meth:`list`.
        """
        out = self._nq._request("GET", "/api/reports/download", params={"key": key})
        return out["url"]


__all__ = ["Reports"]
