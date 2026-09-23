"""Every shipped notebook must be valid, parseable JSON (nbformat 4).

Covers 01_quickstart, 02_yield_curve, 03_portfolio_var, 04_ask_the_ontology,
05_research_loop (added 41-04 — the end-to-end research-loop demo)."""
from __future__ import annotations

import glob
import json
import os

_HERE = os.path.dirname(__file__)
_NOTEBOOK_GLOB = os.path.join(_HERE, "..", "notebooks", "*.ipynb")


def test_notebooks_are_valid_json():
    paths = sorted(glob.glob(_NOTEBOOK_GLOB))
    assert len(paths) == 5, f"expected 5 notebooks, found {len(paths)}"
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            nb = json.load(fh)
        assert nb["nbformat"] == 4
        assert isinstance(nb["cells"], list) and nb["cells"]
