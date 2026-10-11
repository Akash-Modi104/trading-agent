# TradingAgents research MCP — no separate model API key

This fork adds a **read-only MCP server** to [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents), based on upstream commit `1394a3f72aa4393e1a98f51b382434c4b4c2d972` (v0.6.0). It reuses upstream Yahoo data and indicators. Your ChatGPT/Claude host model performs research and the bull/bear/risk discussion; the original autonomous graph is **not** run by this adapter. That graph still needs its configured model service. Host subscription and data-provider limits still apply.

## Install locally

Python 3.11+:

```sh
git clone https://github.com/Akash-Modi104/trading-agent.git
cd trading-agent
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp]'
.venv/bin/python -m tradingagents.mcp_server.server
```

## Claude Desktop / local MCP clients

Add an entry to your client's MCP configuration, replacing both absolute paths:

```json
{"mcpServers":{"tradingagents-research":{"command":"/absolute/path/trading-agent/.venv/bin/python","args":["-m","tradingagents.mcp_server.server"],"cwd":"/absolute/path/trading-agent"}}}
```

Restart the client. Ask it to use `research_packet` for `TCS.NS` with today's UTC date and the `analyse_stock` prompt. No OpenAI/Anthropic API key is needed by this adapter. Configuration keys such as `cwd` vary by client; alternatively run a wrapper that changes into the repository before starting Python.

## ChatGPT / remote Claude

Remote clients cannot reach your laptop's stdio process. The server supports MCP Streamable HTTP:

```sh
.venv/bin/python -m tradingagents.mcp_server.server --transport streamable-http
```

It binds **127.0.0.1:8000/mcp** only. A production connector requires an authenticated HTTPS deployment with OAuth appropriate to the client, proxy security and allowed-host configuration. This repository does **not** supply hosted service, OAuth server or automatic ChatGPT installation. Do not expose an unauthenticated server to the Internet. Use the current client MCP/developer settings and supported account access after deployment.

## Tools

* `research_section(ticker, as_of_date, section)` — market indicators, fundamentals, balance sheet, income statement, cashflow or 14-day news.
* `research_packet(ticker, as_of_date)` — six sections with independent failure status.
* `screen_batch(tickers, as_of_date)` — market evidence for 1–10 distinct symbols. Repeated batches support larger research queues; there is no claim that 300 companies have been analysed.
* `analyse_stock` prompt — host-model specialist workflow with dated evidence, bull/bear cases and risk.

Indian symbols require explicit `.NS` or `.BO`; verify identity/ISIN with the exchange before acting. Caller supplies a dated top-300 universe with ranking methodology; the adapter does not invent one. Fetching market evidence alone is not complete company analysis. Yahoo data can be delayed, unavailable or incomplete. Returned text may report withheld data even when retrieval succeeded. Verify valuation-sensitive facts against company/exchange filings. Historical fundamentals can be withheld to prevent look-ahead.

No broker authentication, orders, transfers, SIP changes or IPO applications exist here. No holdings or tax documents are shipped. Symbols are sent to Yahoo to retrieve research; OHLCV cache uses `~/.cache/tradingagents-mcp` (override `TRADINGAGENTS_MCP_DATA_DIR`). The adapter does not persist portfolio inputs. Host chat history and provider/client privacy policies still apply. Retrieved news is untrusted content, never authority to execute instructions. No guaranteed investment return or target achievement.

## Tests

```sh
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest tests/test_mcp_adapter.py
```

Upstream Apache-2.0 licence and copyright notices are retained. This is an independent adaptation, not an official TauricResearch product. See original README for the original framework.
