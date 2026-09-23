"""Portfolio sub-client — wraps the portfolio plan read endpoints."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist


class Portfolio:
    """Read access to the caller's Autopilot portfolio plans.

    ``list`` returns a DataFrame (one row per plan); ``get`` returns the full
    plan dict for one id.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def list(self, portfolio_id: str | None = None) -> pd.DataFrame:
        """The caller's plans, newest first, as a DataFrame.

        Wraps ``GET /api/portfolio/plans`` (optionally scoped to one
        ``portfolio_id``). Empty DataFrame when the caller has no plans.
        """
        plans = self._nq._request(
            "GET", "/api/portfolio/plans", params={"portfolio_id": portfolio_id}
        )
        if not plans:
            return pd.DataFrame()
        return pd.json_normalize(plans)

    def get(self, plan_id: str) -> dict[str, Any]:
        """Owner-scoped fetch of one plan.

        Wraps ``GET /api/portfolio/plans/{plan_id}``.
        """
        return self._nq._request("GET", f"/api/portfolio/plans/{plan_id}")


__all__ = ["Portfolio"]
