"""Nyquist — Python SDK for the Nyquist agent research desk and quant API.

Quickstart::

    from nyquist import Nyquist

    nq = Nyquist()                       # reads NYQUIST_API_KEY from the env
    df = nq.marketdata.history("NVDA")   # date-indexed OHLCV DataFrame
    ans = nq.ontology.ask("largest counterparty exposure?")
    print(ans.answer)
    call = nq.desk.debate("NVDA")        # bull vs bear, then a verdict
"""
from __future__ import annotations

from .client import Nyquist
from .desk import Debate, Turn
from .errors import NyquistError
from .ontology import AskResult
from .tools import ToolSearch

__version__ = "0.5.0"
__all__ = ["AskResult", "Debate", "Nyquist", "NyquistError", "ToolSearch", "Turn", "__version__"]
