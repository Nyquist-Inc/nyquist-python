"""Desk sub-client — the bull/bear debate over one instrument.

Wraps ``POST /api/agents/committee/bull-bear`` (API key, SSE). One
agent argues the bull case, one the bear case, for ``rounds`` rounds, each
seeing the other's last argument; then a judge rules. The stream is consumed
here and returned as one :class:`Debate`; pass ``on_turn`` to see each turn as
it lands.

Honesty: a turn whose agent failed carries ``error`` and empty ``text``; a
debate without a ruling has ``verdict == ""`` and ``complete is False``, and
``ended`` tells a judge that returned nothing (``True``) from a stream cut off
before the end (``False``). Nothing is filled in on the client side.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Nyquist

DEBATE_PATH = "/api/agents/committee/bull-bear"
SIDES = ("bull", "bear", "judge")


@dataclass(frozen=True)
class Turn:
    """One argument (``bull`` / ``bear``) or the ruling (``judge``)."""

    side: str
    text: str
    round: int | None = None
    #: The persona key the server used — a code identifier, kept out of the
    #: repr so printing a debate never shows it as a label.
    agent_id: str = field(default="", repr=False)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"side": self.side, "round": self.round, "text": self.text, "error": self.error}


@dataclass(frozen=True)
class Debate:
    instrument: str
    rounds: int
    turns: tuple[Turn, ...] = ()
    verdict: str = ""
    #: The server closed the debate (``debate_done``). ``False`` with an empty
    #: verdict means the stream stopped early, not that the judge declined.
    ended: bool = False

    @property
    def complete(self) -> bool:
        """The judge ruled. See ``ended`` for why it did not."""
        return bool(self.verdict)

    @property
    def failed_turns(self) -> tuple[Turn, ...]:
        return tuple(t for t in self.turns if t.error)

    def as_dict(self) -> dict[str, Any]:
        return {
            "instrument": self.instrument,
            "rounds": self.rounds,
            "complete": self.complete,
            "ended": self.ended,
            "verdict": self.verdict,
            "turns": [t.as_dict() for t in self.turns],
        }


def _turn(payload: dict[str, Any]) -> Turn:
    raw_round = payload.get("round")
    return Turn(
        side=str(payload.get("side") or ""),
        text=str(payload.get("text") or "").strip(),
        round=int(raw_round) if isinstance(raw_round, int) else None,
        agent_id=str(payload.get("agent_id") or ""),
        error=str(payload["error"]) if payload.get("error") else None,
    )


class Desk:
    """The agent research desk: give it a ticker, get an argued call back."""

    def __init__(self, nq: Nyquist) -> None:
        self._nq = nq

    def debate(
        self,
        instrument: str,
        *,
        rounds: int = 2,
        language: str = "en",
        on_turn: Callable[[Turn], None] | None = None,
        bull_id: str | None = None,
        bear_id: str | None = None,
        judge_id: str | None = None,
    ) -> Debate:
        """Run a bull/bear debate on ``instrument`` and return it whole.

        ``rounds`` is 1–5 (the server validates). ``language`` is ``en`` or
        ``ru``. Takes minutes, not seconds: every turn is a model call.
        Raises :class:`~nyquist.errors.NyquistError` when the server refuses
        (no key, quota, agents runtime disabled — the reason is in ``detail``).
        """
        overrides = {"bull_id": bull_id, "bear_id": bear_id, "judge_id": judge_id}
        body = {
            "instrument": instrument,
            "rounds": rounds,
            "language": language,
            **{k: v for k, v in overrides.items() if v},
        }

        debate = Debate(instrument=instrument, rounds=rounds)
        for event, payload in self._nq._stream_events(DEBATE_PATH, json_body=body):
            if event == "agent_done" and payload.get("side") in SIDES:
                turn = _turn(payload)
                debate = replace(debate, turns=(*debate.turns, turn))
                if on_turn is not None:
                    on_turn(turn)
            elif event == "debate_done":
                verdict = str(payload.get("verdict") or "").strip()
                debate = replace(debate, verdict=verdict, ended=True)
        return debate


__all__ = ["DEBATE_PATH", "Debate", "Desk", "Turn"]
