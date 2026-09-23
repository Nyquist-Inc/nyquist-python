"""The registry entry, the README marker and the package versions agree.

The MCP Registry rejects a ``server.json`` whose description exceeds 100
characters, and verifies PyPI ownership by finding ``mcp-name: <name>`` in the
package README. Both fail only at publish time, after the PyPI upload — so
they are checked here, next to the version pins that drift on every release.
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from nyquist_mcp import __version__

ROOT = Path(__file__).resolve().parents[1]
SERVER = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_registry_field_limits():
    assert re.fullmatch(r"[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+", SERVER["name"])
    assert 1 <= len(SERVER["description"]) <= 100
    assert 1 <= len(SERVER["title"]) <= 100


def test_readme_carries_the_ownership_marker_for_this_name():
    # The token must end at a boundary (space, newline, tag or -->), not a period.
    assert re.search(rf"mcp-name: {re.escape(SERVER['name'])}(\s|-->|<)", README)


def test_every_version_is_the_same_release():
    package = SERVER["packages"][0]
    assert package["identifier"] == PYPROJECT["project"]["name"]
    assert {SERVER["version"], package["version"], PYPROJECT["project"]["version"],
            __version__} == {__version__}


def test_the_sdk_pin_admits_this_release():
    sdk = next(d for d in PYPROJECT["project"]["dependencies"] if d.startswith("nyquist-sdk"))
    major_minor = ".".join(__version__.split(".")[:2])
    assert f">={major_minor}" in sdk
