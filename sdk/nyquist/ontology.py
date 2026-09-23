"""Ontology sub-client — the semantic layer over ``/api/ontology/*``."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .client import Nyquist


@dataclass
class AskResult:
    """A grounded natural-language answer plus its supporting rows.

    ``answer`` is the synthesised prose; ``rows`` is a DataFrame built from the
    retrieved ontology objects (empty when nothing matched). ``error`` is set
    in-band when the backend degraded (LLM/ClickHouse down) — the answer is
    never fabricated.
    """

    answer: str
    rows: pd.DataFrame
    query: str = ""
    intent: str | None = None
    n_results: int = 0
    model_id: str = ""
    provider: str = ""
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def __str__(self) -> str:
        return self.answer


class Ontology:
    """The semantic layer: ask grounded questions, or search by similarity."""

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def ask(self, query: str, language: str = "en") -> AskResult:
        """Answer a natural-language question grounded in ontology state.

        Wraps ``POST /api/ontology/query/ask``. Returns an :class:`AskResult`
        exposing ``.answer`` (prose) and ``.rows`` (the retrieved objects as a
        DataFrame).
        """
        data = self._nq._request(
            "POST",
            "/api/ontology/query/ask",
            json_body={"query": query, "language": language},
        )
        results = data.get("results") or []
        rows = pd.json_normalize(results) if results else pd.DataFrame()
        return AskResult(
            answer=data.get("answer", ""),
            rows=rows,
            query=data.get("query", query),
            intent=data.get("intent"),
            n_results=data.get("n_results", len(results)),
            model_id=data.get("model_id", ""),
            provider=data.get("provider", ""),
            error=data.get("error"),
            raw=data,
        )

    def search(
        self, query: str, k: int = 10, kind: str | None = None
    ) -> pd.DataFrame:
        """Vector semantic search over ontology objects.

        Wraps ``POST /api/ontology/search/semantic``. Returns a DataFrame of the
        nearest objects with a ``distance`` column (lower = more similar), sorted
        ascending. Empty when embeddings are unconfigured or nothing matched —
        clients then fall back to :meth:`ask`.
        """
        hits = self._nq._request(
            "POST",
            "/api/ontology/search/semantic",
            json_body={"query": query, "k": k, "kind": kind},
        )
        if not hits:
            return pd.DataFrame()
        objects = pd.json_normalize([h["object"] for h in hits])
        objects["distance"] = [h["distance"] for h in hits]
        return objects.sort_values("distance").reset_index(drop=True)


__all__ = ["Ontology", "AskResult"]
