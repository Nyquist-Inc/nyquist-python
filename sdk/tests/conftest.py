"""Shared test helpers — hermetic httpx MockTransport, no network."""
from __future__ import annotations

from collections.abc import Callable

import httpx

from nyquist import Nyquist

Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler) -> Nyquist:
    """Build a :class:`Nyquist` whose transport is an in-memory mock.

    The SDK injects the ``X-API-Key`` header itself (the transport carries no
    auth), so header-injection is genuinely exercised.
    """
    return Nyquist(
        api_key="nyquist_test-key",
        base_url="https://api.test",
        transport=httpx.MockTransport(handler),
    )
