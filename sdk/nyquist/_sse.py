"""Server-sent events → ``(event, data)`` pairs.

The agents runtime streams as ``text/event-stream``: one ``event:`` line, one
``data:`` line of JSON, a blank line. The parser follows the spec loosely
enough for that producer and strictly enough not to invent an event: a frame
without ``data`` is dropped, a ``data`` that is not a JSON object is passed
through under ``{"raw": …}`` instead of being guessed at.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

Event = tuple[str, dict[str, Any]]

#: The only line terminators SSE knows. ``str.splitlines`` — and httpx's
#: ``iter_lines``, built on it — also break on U+2028, U+2029 and U+0085, which
#: the producer leaves unescaped (``ensure_ascii=False``): one such character in
#: a model's argument split its ``data:`` line and the turn vanished.
_EOL = re.compile(r"\r\n|\r|\n")


def iter_lines(chunks: Iterable[str]) -> Iterator[str]:
    """Decoded text chunks → lines, split on SSE terminators only.

    A trailing ``\\r`` is held back until the next chunk: it may be the first
    half of a ``\\r\\n`` cut by the chunk boundary, and treating it as a line
    end would forge an empty line — which ends a frame.
    """
    pending = ""
    for chunk in chunks:
        pending += chunk
        held = "\r" if pending.endswith("\r") else ""
        *lines, rest = _EOL.split(pending[: len(pending) - len(held)])
        pending = rest + held
        yield from lines
    if pending:
        *lines, last = _EOL.split(pending)
        yield from lines
        if last:
            yield last


def _decode(data: str) -> dict[str, Any]:
    try:
        parsed = json.loads(data)
    except ValueError:
        return {"raw": data}
    return parsed if isinstance(parsed, dict) else {"raw": parsed}


def parse_sse(lines: Iterable[str]) -> Iterator[Event]:
    """Yield one ``(event, data)`` per complete frame; ``event`` defaults to ``message``."""
    event = "message"
    data: tuple[str, ...] = ()
    for line in lines:
        if line == "":
            if data:
                yield event, _decode("\n".join(data))
            event, data = "message", ()
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if field == "event":
            event = value
        elif field == "data":
            data = (*data, value)
    if data:
        yield event, _decode("\n".join(data))


__all__ = ["Event", "iter_lines", "parse_sse"]
