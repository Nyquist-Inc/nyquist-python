"""Error types for the Nyquist SDK."""
from __future__ import annotations


class NyquistError(RuntimeError):
    """Any failure talking to the Nyquist API.

    Carries the HTTP ``status_code`` (``None`` for client-side failures such as
    a missing API key or a transport error) plus a human-readable ``detail``.
    Callers never silently consume an error page.
    """

    def __init__(self, status_code: int | None, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        if status_code is None:
            super().__init__(f"Nyquist client error: {detail}")
        else:
            super().__init__(f"Nyquist API {status_code}: {detail}")


__all__ = ["NyquistError"]
