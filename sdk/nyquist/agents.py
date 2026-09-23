"""Agents sub-client — wraps ``/api/agents/*`` (persona roster + chat)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Nyquist


class Agents:
    """Persona roster + single-turn chat. Reachable with an API key;
    model calls count against the caller's quota.
    """

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def list(self, tier: str | None = None) -> list[dict[str, Any]]:
        """The full persona roster (optionally filtered by ``tier``).

        Wraps ``GET /api/agents/list``.
        """
        return self._nq._request(
            "GET", "/api/agents/list", params={"tier": tier}
        )

    def chat(
        self, agent_id: str, message: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """One chat turn against ``agent_id``.

        Wraps ``POST /api/agents/{agent_id}/chat``. Returns the backend's
        ``ChatResponse`` dict verbatim — ``text`` (the reply),
        ``model_id``, ``provider``, ``prompt_tokens``/``completion_tokens``,
        ``tool_calls``. When ``session_id`` is set, turn history is
        loaded/persisted server-side (Redis, 48h TTL) so the same id
        continues the conversation on the next call.
        """
        body: dict[str, Any] = {"message": message}
        if session_id is not None:
            body["session_id"] = session_id
        return self._nq._request(
            "POST", f"/api/agents/{agent_id}/chat", json_body=body
        )


__all__ = ["Agents"]
