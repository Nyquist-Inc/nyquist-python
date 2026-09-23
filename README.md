# Nyquist — Python SDK, CLI and MCP server

The agent research desk for funds under $500M AUM, from Python, the terminal
and any MCP client. Give it a ticker: one agent argues the bull case, one the
bear case, a judge rules, and the reasoning comes back with the call.

| Directory | Package | What it is |
|---|---|---|
| [`sdk/`](sdk/) | [`nyquist-sdk`](https://pypi.org/project/nyquist-sdk/) | Python client (`import nyquist`) and the `nyq` command |
| [`mcp/`](mcp/) | [`nyquist-mcp`](https://pypi.org/project/nyquist-mcp/) | MCP server for Claude, Cursor and other clients (`uvx nyquist-mcp`) |

```bash
pip install nyquist-sdk     # SDK + nyq
uvx nyquist-mcp             # MCP server over stdio
```

Every call goes to the Nyquist API with your own key and returns what the
platform computed; nothing is estimated on the client side. Nyquist is in
closed beta, by invitation — API keys are issued in the portal at
nyquist.pro/settings/api; write to contact@nyquist.pro for access. Desk output
is research, not investment advice.

## Develop

```bash
pip install -e 'sdk[dev]' -e 'mcp[dev]'
python -m pytest sdk/tests -q
python -m pytest mcp/tests -q
```

Tests are hermetic: mocked HTTP, an in-process MCP client, no network.

## Release

Push a tag `vX.Y.Z` that matches the versions in `sdk/pyproject.toml`,
`mcp/pyproject.toml` and `mcp/server.json`. The `release` workflow tests,
builds and uploads both packages to PyPI through trusted publishing — the SDK
first, because the MCP server depends on it.

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
