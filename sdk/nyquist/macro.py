"""Macro sub-client — wraps ``/api/macro-data/*`` (FRED / ECB / Bank of Russia)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist


class Macro:
    """Macro & rates series — FRED, ECB (Frankfurter) and Bank of Russia.

    Wraps ``/api/macro-data`` (API key).
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def fred(self, series_id: str, **params: Any) -> pd.DataFrame:
        """FRED economic series observations, date-indexed.

        Wraps ``GET /api/macro-data/fred/series``. ``params`` forwards
        ``limit``/``sort_order``/``observation_start``/``observation_end``
        verbatim to the handler. Empty (never fabricated) DataFrame when
        the series has no rows for the window.
        """
        data = self._nq._request(
            "GET",
            "/api/macro-data/fred/series",
            params={"series_id": series_id, **params},
        )
        return _observations_to_frame(data.get("observations", []))

    def ecb_history(self, **params: Any) -> pd.DataFrame:
        """Historical ECB exchange rates (Frankfurter), date-indexed.

        Wraps ``GET /api/macro-data/ecb/history`` — pass ``start``
        (required, ``YYYY-MM-DD``), plus optional ``base``/``end``/
        ``symbols`` verbatim. Columns are the quote currencies.
        """
        data = self._nq._request(
            "GET", "/api/macro-data/ecb/history", params=params
        )
        return _rates_to_frame(data.get("rates", {}))

    def cbr_key_rate(self) -> dict[str, Any]:
        """Current CBR key rate + history.

        Wraps ``GET /api/macro-data/cbr/key-rate``.
        """
        return self._nq._request("GET", "/api/macro-data/cbr/key-rate")


def _observations_to_frame(observations: list[dict[str, Any]]) -> pd.DataFrame:
    """Shape FRED ``{date, value}`` observations into a date-indexed frame."""
    if not observations:
        empty = pd.DataFrame(columns=["value"])
        empty.index = pd.DatetimeIndex([], name="date")
        return empty
    df = pd.DataFrame(observations)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()[["value"]]


def _rates_to_frame(rates: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Shape a Frankfurter ``{date: {currency: rate}}`` map into a frame."""
    if not rates:
        empty = pd.DataFrame()
        empty.index = pd.DatetimeIndex([], name="date")
        return empty
    df = pd.DataFrame.from_dict(rates, orient="index")
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    return df.sort_index()


__all__ = ["Macro"]
