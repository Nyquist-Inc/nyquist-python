"""Light matplotlib helpers for the research notebooks.

matplotlib is imported lazily inside each helper so the core SDK installs and
runs without the ``[plot]`` extra. Install with ``pip install 'nyquist[plot]'``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .errors import NyquistError

if TYPE_CHECKING:
    import pandas as pd


def _plt() -> Any:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without matplotlib
        raise NyquistError(
            None,
            "matplotlib is not installed — run `pip install 'nyquist[plot]'`.",
        ) from exc
    return plt


def price(df: pd.DataFrame, column: str = "close", title: str | None = None) -> Any:
    """Line-plot one column of an OHLCV history DataFrame; returns the Axes."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df[column])
    ax.set_title(title or f"{df.attrs.get('ticker', '')} {column}".strip())
    ax.set_xlabel("date")
    ax.set_ylabel(column)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return ax


def curve(tenors: list[Any], yields: list[float], title: str = "Yield curve") -> Any:
    """Plot a term structure (tenor -> yield); returns the Axes."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(range(len(tenors)), yields, marker="o")
    ax.set_xticks(range(len(tenors)))
    ax.set_xticklabels([str(t) for t in tenors])
    ax.set_title(title)
    ax.set_xlabel("tenor")
    ax.set_ylabel("yield (%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return ax


__all__ = ["price", "curve"]
