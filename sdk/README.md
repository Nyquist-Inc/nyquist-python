# Nyquist Python SDK and `nyq` CLI

The agent research desk for funds under $500M AUM, from Python and the
terminal. Give it a ticker: one agent argues the bull case, one the bear case,
a judge rules, and the reasoning comes back with the call. The same client
reaches reconciled market data, VaR, the ontology of your book, and hundreds of
governed read-or-compute tools.

> Nyquist is in closed beta, by invitation. API keys are issued in the portal
> at nyquist.pro/settings/api. Write to contact@nyquist.pro for access.
> Desk output is research, not investment advice.

```bash
pip install nyquist-sdk            # imports as `nyquist`, installs the `nyq` command
pip install 'nyquist-sdk[plot]'    # + matplotlib helpers
pip install 'nyquist-sdk[mcp]'     # + the MCP server for Claude, Cursor and other clients
```

Python 3.11+.

## From the terminal

```bash
nyq login                          # verify a key with the API, save it to ~/.nyquist/config.json (0600)
nyq desk NVDA                      # bull vs bear, streamed turn by turn, then the verdict
nyq desk NVDA --rounds 3 --json    # the whole debate as JSON
nyq quote NVDA                     # latest quote, JSON
nyq history NVDA --days 30 > nvda.csv
nyq tools search yield curve       # search the governed tool surface
nyq tools call api.zcyc.get        # run one tool, print its JSON
nyq doctor                         # health · tools · agents, each ok / fail / skipped with a reason
nyq mcp                            # serve the MCP tools over stdio (needs the [mcp] extra)
```

Configuration, first match wins: `--base-url` / `--api-key`, then
`NYQUIST_BASE_URL` / `NYQUIST_API_KEY`, then `~/.nyquist/config.json`.

Data goes to stdout (CSV or JSON, pipeable); commentary and refusals go to
stderr. Exit codes: `0` done · `1` the platform refused or returned nothing ·
`2` usage or configuration error · `3` (`doctor`) some checks skipped, none
failed. An empty answer is reported as empty — `nyq history` on a symbol with
no bars exits `1` instead of printing an empty CSV.

## From Python

```python
from nyquist import Nyquist

nq = Nyquist()                                  # reads NYQUIST_API_KEY

debate = nq.desk.debate("NVDA", rounds=2, on_turn=lambda t: print(t.side, t.text[:80]))
debate.verdict                                  # "" when the judge gave no ruling
debate.complete                                 # False in that case — never filled in

df = nq.marketdata.history("NVDA", days=365)    # date-indexed OHLCV DataFrame
var = nq.risk.symbol_var(["NVDA", "AAPL"], "2025-09-01", "2026-09-01",
                         weights=[0.6, 0.4], method="historical", confidence=0.99)

ans = nq.ontology.ask("Which counterparty carries our largest exposure?")
ans.answer, ans.rows                            # grounded answer + supporting objects

hits = nq.tools.search("zero coupon curve")
curve = nq.tools.execute(hits.results[0]["tool_id"])
```

| Call | Wraps | Returns |
|------|-------|---------|
| `nq.desk.debate(instrument, rounds=2, language="en", on_turn=None)` | `POST /api/agents/committee/bull-bear` (streamed) | `Debate` (`.turns`, `.verdict`, `.complete`) |
| `nq.marketdata.history(ticker, days=365, source=None)` | `GET /api/market-data/history/{ticker}` | date-indexed OHLCV `DataFrame` |
| `nq.marketdata.price(ticker)` | `GET /api/market-data/stock/{ticker}` | `dict` |
| `nq.marketdata.fx(base, quote="USD")` | `GET /api/market-data/currency/{base}/{quote}` | `dict` |
| `nq.risk.var(returns, method=..., ...)` | `POST /api/risk/var` | `dict` |
| `nq.risk.portfolio_var(tickers, weights, returns_data, ...)` | `POST /api/risk/portfolio-var` | `dict` |
| `nq.risk.symbol_var(symbols, start_date, end_date, ...)` | `POST /api/risk/symbol/var` | `dict` |
| `nq.portfolio.list(portfolio_id=None)` | `GET /api/portfolio/plans` | `DataFrame` |
| `nq.portfolio.get(plan_id)` | `GET /api/portfolio/plans/{plan_id}` | `dict` |
| `nq.ontology.ask(query, language="en")` | `POST /api/ontology/query/ask` | `AskResult` (`.answer`, `.rows`) |
| `nq.ontology.search(query, k=10, kind=None)` | `POST /api/ontology/search/semantic` | `DataFrame` (object + `distance`) |
| `nq.tools.search(words, limit=20)` | `GET /api/ontology/tools/search` | `ToolSearch` (iterable, `.enabled`) |
| `nq.tools.get(tool_id)` | `GET /api/ontology/tools/{tool_id}` | `dict` (path, method, schema, `requires`) |
| `nq.tools.execute(tool_id, params)` | `POST /api/ontology/tools/{tool_id}/execute` | the tool's result |
| `nq.tools.governance()` | `GET /api/ontology/tools/governance` | `dict` (`enabled`, counts) |
| `nq.get(path, **params)` / `nq.post(path, json=...)` | any endpoint your key reaches | parsed JSON |

Every failure raises `NyquistError` with `.status_code` and the server's
`.detail`. The SDK never fabricates data: no data comes back as an empty
frame, a refusal as an exception.

## Authentication

Requests carry your API key in the `X-API-Key` header. Keys look like
`nyquist_<random>` and are minted in the portal at **nyquist.pro/settings/api**.

## Governed tools — bring your own model

`nq.tools`, `nyq tools` and the MCP server's search/describe/call tools all
reach one surface: every read-or-compute endpoint a deny-first policy admits
(no writes, no admin, no streams), discovered by search and executed **as
you** — your key is forwarded, so a tool reads exactly what you can read.

When a deployment has the surface switched off, `search` returns an empty
`ToolSearch` with `enabled=False`, `nyq tools search` says so and exits `1`,
and `nyq doctor` reports `fail tools`. That is a statement about the
deployment, not "no such tool".

Typed shapes of every ontology object kind ship as `nyquist.ontology_types`
(`ObjectKind`, `LinkKind`, one `TypedDict` per kind). The module is generated
from the platform's metadata layer — do not edit it by hand.

## Working from the source repository

The repository copy also carries a VS Code dev container and example
notebooks (`notebooks/`: quickstart, yield curve, portfolio VaR, asking the
ontology, research loop). They ship with empty outputs and run live against
the API.

```bash
pip install -e '.[plot,dev]'
ruff check nyquist/
python -m pytest tests/ -q       # hermetic — httpx MockTransport, no network
```

## License

Apache-2.0 — see `LICENSE` and `NOTICE`.
