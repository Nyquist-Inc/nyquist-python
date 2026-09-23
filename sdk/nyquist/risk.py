"""Risk sub-client — wraps ``/api/risk/*`` (VaR / CVaR engine)."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Nyquist


class Risk:
    """GARCH-conditional VaR / CVaR over return series or ticker books."""

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def var(
        self,
        returns: list[float],
        *,
        method: str = "parametric",
        confidence: float = 0.95,
        horizon: int = 1,
        portfolio_value: float = 1.0,
        n_simulations: int = 10_000,
        use_garch: bool = False,
        garch_model: str = "garch_11",
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Single-method VaR/CVaR on a caller-supplied return series.

        Wraps ``POST /api/risk/var``. ``method`` is one of ``parametric``,
        ``historical`` or ``monte_carlo``.
        """
        body = {
            "returns": list(returns),
            "method": method,
            "confidence": confidence,
            "horizon": horizon,
            "portfolio_value": portfolio_value,
            "n_simulations": n_simulations,
            "use_garch": use_garch,
            "garch_model": garch_model,
            "seed": seed,
        }
        return self._nq._request("POST", "/api/risk/var", json_body=_drop_none(body))

    def portfolio_var(
        self,
        tickers: list[str],
        weights: list[float],
        returns_data: dict[str, list[float]],
        *,
        confidence_level: float = 0.99,
        portfolio_value: float = 1_000_000.0,
    ) -> dict[str, Any]:
        """Historical VaR/CVaR for a weighted book.

        Wraps ``POST /api/risk/portfolio-var``. ``tickers`` and ``weights`` are
        zipped into the ``portfolio_weights`` map; ``returns_data`` maps each
        symbol to its daily return series.
        """
        if len(tickers) != len(weights):
            from .errors import NyquistError

            raise NyquistError(
                None,
                f"tickers ({len(tickers)}) and weights ({len(weights)}) "
                "must be the same length",
            )
        body = {
            "portfolio_weights": dict(zip(tickers, weights, strict=True)),
            "returns_data": returns_data,
            "confidence_level": confidence_level,
            "portfolio_value": portfolio_value,
        }
        return self._nq._request("POST", "/api/risk/portfolio-var", json_body=body)

    def symbol_var(
        self,
        symbols: list[str],
        start_date: str | datetime,
        end_date: str | datetime,
        *,
        weights: list[float] | None = None,
        method: str = "parametric",
        confidence: float = 0.95,
        horizon: int = 1,
        portfolio_value: float = 1.0,
        use_garch: bool = False,
        garch_model: str = "garch_11",
    ) -> dict[str, Any]:
        """VaR/CVaR with returns auto-fetched from the Golden Record store.

        Wraps ``POST /api/risk/symbol/var`` — pass tickers + a date window and
        the backend pulls verified returns itself (no need to supply series).
        """
        body = {
            "symbols": list(symbols),
            "start_date": _iso(start_date),
            "end_date": _iso(end_date),
            "method": method,
            "confidence": confidence,
            "horizon": horizon,
            "portfolio_value": portfolio_value,
            "weights": weights,
            "use_garch": use_garch,
            "garch_model": garch_model,
        }
        return self._nq._request(
            "POST", "/api/risk/symbol/var", json_body=_drop_none(body)
        )


def _drop_none(body: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` fields so the backend applies its own defaults."""
    return {k: v for k, v in body.items() if v is not None}


def _iso(value: str | datetime) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


__all__ = ["Risk"]
