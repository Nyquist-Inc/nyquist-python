"""Market-data sub-client — wraps ``/api/market-data/*``."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist

_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class MarketData:
    """Prices, FX and reconciled OHLCV history.

    Returns a date-indexed pandas DataFrame for the tabular ``history`` call;
    point quotes (``price``, ``fx``) come back as plain dicts.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def history(
        self, ticker: str, days: int = 365, source: str | None = None
    ) -> pd.DataFrame:
        """Daily OHLCV for ``ticker`` from the Golden Record store.

        Wraps ``GET /api/market-data/history/{ticker}?lookback_days=&source=``.
        Returns a DataFrame indexed by ``date`` (a ``DatetimeIndex``) with
        ``open/high/low/close/volume`` columns. Empty (never fabricated) when the
        store has no data for the symbol/window yet.
        """
        data = self._nq._request(
            "GET",
            f"/api/market-data/history/{ticker}",
            params={"lookback_days": days, "source": source},
        )
        return _bars_to_frame(
            data.get("bars", []),
            ticker=data.get("ticker", ticker.upper()),
            source=data.get("source"),
        )

    def price(self, ticker: str) -> dict[str, Any]:
        """Latest quote + fundamentals for one equity.

        Wraps ``GET /api/market-data/stock/{ticker}``.
        """
        return self._nq._request("GET", f"/api/market-data/stock/{ticker}")

    def fx(self, base: str, quote: str = "USD") -> dict[str, Any]:
        """Spot rate for a currency pair.

        Wraps ``GET /api/market-data/currency/{base}/{quote}``.
        """
        return self._nq._request("GET", f"/api/market-data/currency/{base}/{quote}")


def _bars_to_frame(
    bars: list[dict[str, Any]], *, ticker: str, source: str | None
) -> pd.DataFrame:
    """Shape a list of OHLCV bar dicts into a date-indexed DataFrame."""
    if not bars:
        empty = pd.DataFrame(columns=_OHLCV_COLUMNS)
        empty.index = pd.DatetimeIndex([], name="date")
        empty.attrs.update(ticker=ticker, source=source)
        return empty

    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    # Keep a stable column order; tolerate feeds that omit a column.
    cols = [c for c in _OHLCV_COLUMNS if c in df.columns]
    df = df[cols]
    df.attrs.update(ticker=ticker, source=source)
    return df


__all__ = ["MarketData"]
