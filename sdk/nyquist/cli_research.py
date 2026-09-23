"""``nyq quote`` / ``nyq history`` / ``nyq desk`` — research verbs for the terminal.

Kept apart from :mod:`nyquist.cli`, which owns configuration, the parser and
the governed-tools verbs. Every handler has the same shape as there:
``(args, settings, transport, out, err) -> exit code``.

Output rules: data goes to ``out`` (pipeable — CSV or JSON), commentary and
refusals to ``err``. An empty answer is reported as empty, never padded.
"""
from __future__ import annotations

import json
from typing import IO, TYPE_CHECKING, Any

from .client import Nyquist
from .desk import Turn

if TYPE_CHECKING:
    import httpx

    from .cli import Settings

EXIT_OK = 0
EXIT_FAIL = 1

_SIDE_LABEL = {"bull": "BULL", "bear": "BEAR", "judge": "VERDICT"}


def _client(settings: Settings, transport: httpx.BaseTransport | None) -> Nyquist:
    return Nyquist(api_key=settings.api_key, base_url=settings.base_url, transport=transport)


def _dump(data: Any, out: IO[str]) -> None:
    json.dump(data, out, indent=2, default=str)
    out.write("\n")


def cmd_quote(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    with _client(settings, transport) as nq:
        _dump(nq.marketdata.price(args.ticker), out)
    return EXIT_OK


def cmd_history(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    with _client(settings, transport) as nq:
        frame = nq.marketdata.history(args.ticker, days=args.days)
    if frame.empty:
        print(f"no daily bars for {args.ticker.upper()} in the last {args.days} days", file=err)
        return EXIT_FAIL
    if args.json:
        records = frame.reset_index().to_dict(orient="records")
        _dump({"ticker": frame.attrs.get("ticker"), "source": frame.attrs.get("source"),
               "bars": records}, out)
    else:
        frame.to_csv(out, date_format="%Y-%m-%d")
    return EXIT_OK


def _print_turn(turn: Turn, out: IO[str]) -> None:
    label = _SIDE_LABEL.get(turn.side, turn.side.upper())
    if turn.round is not None:
        label = f"{label} · round {turn.round}"
    body = turn.text if not turn.error else f"(no argument — {turn.error})"
    print(f"── {label}\n{body}\n", file=out, flush=True)


def cmd_desk(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    ticker = args.ticker.upper()
    if not args.json:
        print(f"Bull vs bear on {ticker}, {args.rounds} round(s). Each turn is a model "
              "call — this takes minutes.\n", file=err, flush=True)
    on_turn = None if args.json else (lambda turn: _print_turn(turn, out))
    with _client(settings, transport) as nq:
        debate = nq.desk.debate(ticker, rounds=args.rounds, language=args.lang, on_turn=on_turn)
    if args.json:
        _dump(debate.as_dict(), out)
    if debate.complete:
        return EXIT_OK
    failed = len(debate.failed_turns)
    if debate.ended:
        judge = next((t for t in debate.turns if t.side == "judge"), None)
        reason = f": {judge.error}" if judge and judge.error else ""
        print(f"no verdict: the judge returned no ruling{reason} "
              f"({failed} of {len(debate.turns)} turns failed)", file=err)
    else:
        print(f"no verdict: the stream ended before the debate closed "
              f"({len(debate.turns)} turns received)", file=err)
    return EXIT_FAIL


def add_research_commands(sub) -> None:
    """Register the research verbs on the top-level subparsers."""
    quote = sub.add_parser("quote", help="latest quote for one ticker (JSON)")
    quote.add_argument("ticker")
    quote.set_defaults(handler=cmd_quote)

    history = sub.add_parser("history", help="daily OHLCV for one ticker (CSV, or --json)")
    history.add_argument("ticker")
    history.add_argument("--days", type=int, default=365)
    history.add_argument("--json", action="store_true")
    history.set_defaults(handler=cmd_history)

    desk = sub.add_parser("desk", help="bull vs bear debate on a ticker, then a verdict")
    desk.add_argument("ticker")
    desk.add_argument("--rounds", type=int, default=2, choices=range(1, 6), metavar="1-5")
    desk.add_argument("--lang", default="en", choices=("en", "ru"))
    desk.add_argument("--json", action="store_true",
                      help="print the whole debate as JSON at the end")
    desk.set_defaults(handler=cmd_desk)


__all__ = ["add_research_commands", "cmd_desk", "cmd_history", "cmd_quote"]
