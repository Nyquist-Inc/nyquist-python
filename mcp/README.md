# Nyquist MCP server

<!-- mcp-name: com.getnyquist/nyquist -->

The agent research desk for funds under $500M AUM, as tools for Claude, Cursor
and any other MCP client. Give it a ticker: one agent argues the bull case, one
the bear case, a judge rules, and the reasoning comes back with the call. The
same server reaches the rest of the Nyquist platform — market data, VaR, and
hundreds of governed read-or-compute tools found by search.

Every tool calls the Nyquist API with **your own API key** and returns what the
platform computed. Nothing is estimated on the client side: a refusal comes back
as a tool error with the platform's reason, and missing data comes back empty.

> Nyquist is in closed beta, by invitation. API keys are issued in the portal
> at nyquist.pro/settings/api. Write to contact@nyquist.pro for access.
> Desk output is research, not investment advice.

## Install

```bash
uvx nyquist-mcp            # run without installing
pip install nyquist-mcp    # or install; brings the nyquist-sdk package and the `nyq` CLI
```

Python 3.11+. The server speaks MCP over stdio.

## Configure your client

**Claude Desktop** — `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nyquist": {
      "command": "uvx",
      "args": ["nyquist-mcp"],
      "env": { "NYQUIST_API_KEY": "nyquist_..." }
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add nyquist --env NYQUIST_API_KEY=nyquist_... -- uvx nyquist-mcp
```

**Cursor** — `~/.cursor/mcp.json`, same block as Claude Desktop.

The key can also come from `~/.nyquist/config.json`: run `nyq login` once and
leave `env` out. `NYQUIST_BASE_URL` points the server at another deployment.

## Tools

| Tool | What it returns |
|---|---|
| `nyquist_bull_bear_debate` | Bull and bear arguments over 1–5 rounds, then a verdict. Takes minutes; reports progress per turn. `complete: false` when the judge gave no ruling. |
| `nyquist_quote` | Latest quote and fundamentals for one equity. |
| `nyquist_price_history` | Daily OHLCV bars from the reconciled market-data store. |
| `nyquist_value_at_risk` | VaR and CVaR of a basket — parametric, historical or Monte Carlo — on returns the platform fetches itself. |
| `nyquist_ask` | A question answered from the objects in your workspace, with the supporting objects. |
| `nyquist_search_tools` | Search the governed tool surface: pricing, risk, stress, curves, portfolio analytics. |
| `nyquist_describe_tool` | The parameter schema of one governed tool. |
| `nyquist_call_tool` | Run one governed tool as you and return its result verbatim. |

The other seven tools are read-only and marked so. `nyquist_call_tool`
runs whichever governed tool it is given; the surface is admitted by a
deny-first policy (no writes, no admin), but the tool makes no read-only claim,
so your client may ask before each call. Every call runs under your key, so a
tool reaches exactly what you can reach.

## From the terminal

The same package installs `nyq`:

```bash
nyq login                      # verify a key, save it (0600)
nyq desk NVDA                  # the bull/bear debate, streamed
nyq history NVDA --days 30     # CSV to stdout
nyq tools search yield curve   # the governed surface
nyq mcp                        # this server, same as `nyquist-mcp`
```

## Develop

From the root of the source repository (`sdk/` and `mcp/` side by side):

```bash
pip install -e 'sdk[dev]' -e 'mcp[dev]'
python -m pytest mcp/tests -q  # in-process MCP client, mocked HTTP, no network
```

## License

Apache-2.0 — see `LICENSE` and `NOTICE`.
