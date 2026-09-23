"""Crypto sub-client — wraps ``/api/crypto-data/*`` (CoinGecko)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist


class Crypto:
    """Crypto markets, coin charts and global stats via CoinGecko.

    Wraps ``/api/crypto-data`` (API key).
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def markets(self, **params: Any) -> pd.DataFrame:
        """Top crypto markets by market cap.

        Wraps ``GET /api/crypto-data/coingecko/markets`` — pass
        ``vs_currency``/``per_page``/``page``/``order`` verbatim. Empty
        DataFrame when the upstream returns no rows.
        """
        data = self._nq._request(
            "GET", "/api/crypto-data/coingecko/markets", params=params
        )
        return pd.DataFrame(data) if data else pd.DataFrame()

    def chart(
        self, coin_id: str, days: int = 30, vs_currency: str = "usd"
    ) -> pd.DataFrame:
        """Price history for one coin, date-indexed.

        Wraps ``GET /api/crypto-data/coingecko/coin/{id}/chart``. Returns a
        DataFrame with ``price``/``market_cap``/``total_volume`` columns
        (CoinGecko emits epoch-ms series); empty when the coin has no
        history for the window.
        """
        data = self._nq._request(
            "GET",
            f"/api/crypto-data/coingecko/coin/{coin_id}/chart",
            params={"vs_currency": vs_currency, "days": days},
        )
        return _series_to_frame(data)

    def trending(self) -> Any:
        """Trending coins (search interest).

        Wraps ``GET /api/crypto-data/coingecko/trending``.
        """
        return self._nq._request("GET", "/api/crypto-data/coingecko/trending")

    def global_stats(self) -> dict[str, Any]:
        """Global crypto market stats (named ``global_stats`` — ``global``
        is a Python keyword).

        Wraps ``GET /api/crypto-data/coingecko/global``.
        """
        return self._nq._request("GET", "/api/crypto-data/coingecko/global")


_CHART_COLUMNS = ["price", "market_cap", "total_volume"]


def _series_to_frame(data: dict[str, Any]) -> pd.DataFrame:
    """Shape CoinGecko ``{prices, market_caps, total_volumes}`` (epoch-ms
    pairs) into a date-indexed DataFrame."""
    prices = data.get("prices") or []
    if not prices:
        empty = pd.DataFrame(columns=_CHART_COLUMNS)
        empty.index = pd.DatetimeIndex([], name="date")
        return empty
    idx = pd.to_datetime([p[0] for p in prices], unit="ms")
    df = pd.DataFrame({"price": [p[1] for p in prices]}, index=idx)
    df.index.name = "date"
    for col, key in (("market_cap", "market_caps"), ("total_volume", "total_volumes")):
        series = data.get(key) or []
        if len(series) == len(prices):
            df[col] = [s[1] for s in series]
    return df.sort_index()


__all__ = ["Crypto"]
