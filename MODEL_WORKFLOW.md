# Full original workflow using a signed-in model

The MCP data adapter and the original autonomous graph are separate modes. This fork now adds a **`codex` LangChain model provider** that invokes the official Codex CLI using its existing sign-in. It does not extract, copy or publish login credentials. Each call uses ephemeral execution in a temporary directory with read-only sandboxing and ignores user configuration. It asks the CLI to act as a model component; tool requests returned in JSON are checked against the graph's bound tools and executed by the original graph. This is a CLI bridge, not a native OpenAI Chat API endpoint. Model calls consume your Codex allowance and can fail on login, quota, model-access or invalid-output errors.

## Local model-backed MCP

1. Install this fork with `pip install -e '.[mcp]'` in a virtual environment.
2. Install the official Codex CLI, then `codex login` and sign in with ChatGPT. Check `codex login status`.
3. Run:

```sh
python -m tradingagents.mcp_server.server --enable-model
```

Add `--enable-model` to the Python argument list in your local Claude/Codex MCP configuration. Claude can orchestrate the tools while the underlying graph's model calls use the signed-in Codex model. This does not use a Claude subscription for inference. Use `TRADINGAGENTS_CODEX_BIN` if Codex is not on PATH; `TRADINGAGENTS_CODEX_MODEL` optionally selects a model your account supports. Leave it unset to use the CLI's default.

Call `start_model_analysis("TCS.NS", "YYYY-MM-DD")`, then poll `model_analysis_status(job_id)`. The server runs the actual upstream market, sentiment, news and fundamental analysts, bull/bear research debate, research manager, trader proposal, aggressive/conservative/neutral risk debate and portfolio manager. It also uses the original memory/reflection and report generation. There are **no real broker orders**. Reports and memory remain in the configured local cache. One job can run at a time. Background jobs stop if the process exits; status IDs are not durable. Retain report files for completed work.

Model jobs are deliberately restricted to local stdio. A remote ChatGPT server must not spend its operator's account allowance for unauthenticated users. Authenticated per-user deployment is separate work.

## Original Python API, portfolio, backtests and checkpointing

All original graph interfaces remain available with the new model provider:

```python
from copy import deepcopy
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

config = deepcopy(DEFAULT_CONFIG)
config.update(llm_provider="codex", quick_think_llm="", deep_think_llm="")
# Optional original config: checkpoint_enabled, max_debate_rounds,
# max_risk_discuss_rounds, max_tool_rounds, memory_log_path, results_dir.
graph = TradingAgentsGraph(config=config)
state, decision = graph.propagate("TCS.NS", "YYYY-MM-DD")
graph.save_reports(state, "TCS.NS")
```

Pass the original `PortfolioContext` to `propagate(..., portfolio=portfolio)` for private holdings context. Original `run_backtest` accepts the same `config`; its decisions will call the model through this bridge. Reflection, checkpoint resume and backtests retain upstream behavior and limitations. Backtests and large company queues can use substantial model allowance. Their availability is not a claim that all have been tested live or that returns are reliable.

## What a model connection cannot fix

Vendor availability is separate from model access. Yahoo data may be delayed or absent; Indian StockTwits coverage can be absent. Optional FRED/Alpha Vantage and other keyed sources still need their own data keys. No model key is needed for the Codex bridge. Do not replace missing evidence with invented numbers. Keep source dates, costs, tax assumptions and liquidity constraints in every actionable portfolio proposal.
