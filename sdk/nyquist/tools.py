"""Tools sub-client — the governed tool surface (``/api/ontology/tools/*``).

The platform admits ~1400 read-or-compute endpoints to a deny-first policy
(no writes, no admin, no streams) and exposes them as *tools*: search by
words, read one, execute one. Execution runs AS YOU — the gateway forwards
the same B2B key this client sends, so what you can read is what a tool can
read, and nothing more.

The whole surface sits behind ``MANIFEST_TOOLS_ENABLED`` on the gateway. When
it is off, search answers an empty list with ``enabled=False`` rather than
"no match" — :class:`ToolSearch` carries that flag so a caller can tell the
two apart instead of concluding the platform has no such tool.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Nyquist

FLAG = "MANIFEST_TOOLS_ENABLED"


@dataclass
class ToolSearch:
    """Search hits plus the honesty flag.

    Iterating yields the tool views (``tool_id``, ``method``, ``path``,
    ``description``, ``parameters_schema``, ``requires``, ``reason``).
    """

    query: str
    results: list[dict[str, Any]] = field(default_factory=list)
    total_available: int = 0
    #: ``False`` means the surface is switched off on the gateway — nothing is
    #: exposed, so an empty ``results`` says nothing about what exists.
    enabled: bool = True

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __str__(self) -> str:
        if not self.enabled:
            return f"<ToolSearch {self.query!r}: surface disabled ({FLAG} is off on the gateway)>"
        return f"<ToolSearch {self.query!r}: {len(self.results)} of {self.total_available}>"


class Tools:
    """Search, inspect and execute governed tools."""

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def search(self, query: str, limit: int = 20) -> ToolSearch:
        """Rank tools against free-text ``query``.

        Wraps ``GET /api/ontology/tools/search``. An empty query returns
        nothing by design — the catalogue is discovered, not listed.
        """
        data = self._nq._request(
            "GET", "/api/ontology/tools/search", params={"q": query, "limit": limit}
        )
        return ToolSearch(
            query=data.get("query", query),
            results=list(data.get("results") or []),
            total_available=int(data.get("total_available") or 0),
            enabled=bool(data.get("enabled", True)),
        )

    def get(self, tool_id: str) -> dict[str, Any]:
        """One tool's view — path, method, parameter schema, required permission.

        Wraps ``GET /api/ontology/tools/{tool_id}``; raises
        :class:`~nyquist.errors.NyquistError` (404) when the id is not in the
        governed surface, with the gateway's reason in ``detail``.
        """
        return self._nq._request("GET", f"/api/ontology/tools/{tool_id}")

    def execute(self, tool_id: str, params: dict[str, Any] | None = None) -> Any:
        """Run one tool with ``params`` and return its result.

        Wraps ``POST /api/ontology/tools/{tool_id}/execute``. The gateway
        calls the underlying endpoint with THIS client's key, so the result is
        exactly what a direct call would return. Any refusal — unknown tool,
        surface off, missing parameter, upstream 4xx — is a
        :class:`~nyquist.errors.NyquistError` (400) carrying the reason.
        """
        data = self._nq._request(
            "POST",
            f"/api/ontology/tools/{tool_id}/execute",
            json_body={"parameters": dict(params or {})},
        )
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data

    def governance(self) -> dict[str, Any]:
        """What the surface contains, by permission and verb — and whether it is on.

        Wraps ``GET /api/ontology/tools/governance``.
        """
        return self._nq._request("GET", "/api/ontology/tools/governance")


__all__ = ["FLAG", "ToolSearch", "Tools"]
