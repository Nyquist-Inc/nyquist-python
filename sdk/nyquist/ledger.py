"""Execution-ledger sub-client — wraps ``/api/execution-ledger/*``."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist

_TRADE_COLUMNS = [
    "id", "source", "source_ref", "account_id", "instrument", "side",
    "quantity", "price", "notional", "currency", "venue", "counterparty",
    "status", "executed_at", "settlement_date", "details",
]
_POSITION_COLUMNS = [
    "instrument", "source", "net_quantity", "gross_notional",
    "net_notional", "trades", "last_price", "last_executed_at",
]


class ExecutionLedger:
    """Unified execution ledger — the durable union of OTC P2P, TradFi
    broker fills, NCCH external-counterparty trades and RWA primary orders.

    Wraps ``/api/execution-ledger`` (API key). Sync runs on read (throttled,
    idempotent) — no hot-path coupling to any trade booking path.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def trades(self, **params: Any) -> pd.DataFrame:
        """Unified trade blotter.

        Wraps ``GET /api/execution-ledger/trades`` — pass ``source``
        (one of ``OTC_P2P``/``TRADFI``/``NCCH``/``RWA_PRIMARY``),
        ``account_id``, ``instrument``, ``limit``, ``offset`` verbatim.
        Empty-safe: a stable-column DataFrame when the caller has no
        trades yet, never a raise.
        """
        data = self._nq._request(
            "GET", "/api/execution-ledger/trades", params=params
        )
        items = data.get("items", []) if isinstance(data, dict) else data
        if not items:
            return pd.DataFrame(columns=_TRADE_COLUMNS)
        return pd.json_normalize(items)

    def positions(self, account_id: str | None = None) -> pd.DataFrame:
        """Net positions per (instrument, source).

        Wraps ``GET /api/execution-ledger/positions``. Empty-safe:
        stable-column DataFrame when the account has no open positions.
        """
        data = self._nq._request(
            "GET",
            "/api/execution-ledger/positions",
            params={"account_id": account_id},
        )
        if not data:
            return pd.DataFrame(columns=_POSITION_COLUMNS)
        return pd.json_normalize(data)

    def reconciliation(self) -> dict[str, Any]:
        """Origin-store vs ledger counts per source (nonzero lag = sync drift).

        Wraps ``GET /api/execution-ledger/reconciliation``.
        """
        return self._nq._request("GET", "/api/execution-ledger/reconciliation")

    def sources(self) -> Any:
        """The four unioned execution sources.

        Wraps ``GET /api/execution-ledger/sources``.
        """
        return self._nq._request("GET", "/api/execution-ledger/sources")

    def sync(self) -> dict[str, Any]:
        """Force a full (no-watermark) resync from all sources; idempotent.

        Wraps ``POST /api/execution-ledger/sync``.
        """
        return self._nq._request("POST", "/api/execution-ledger/sync")


__all__ = ["ExecutionLedger"]
