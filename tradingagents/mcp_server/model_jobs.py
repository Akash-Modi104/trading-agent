"""Bounded background execution of the original graph, with local reports/memory."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import os
import threading
import uuid

from tradingagents.default_config import DEFAULT_CONFIG

_jobs: dict[str, dict] = {}
_lock = threading.Lock()
_running = False


def model_config():
    root = Path(os.environ.get('TRADINGAGENTS_MCP_DATA_DIR', '~/.cache/tradingagents-mcp')).expanduser()
    config = deepcopy(DEFAULT_CONFIG)
    config.update(llm_provider='codex', quick_think_llm=os.environ.get('TRADINGAGENTS_CODEX_MODEL', ''),
                  deep_think_llm=os.environ.get('TRADINGAGENTS_CODEX_MODEL', ''),
                  max_debate_rounds=1, max_risk_discuss_rounds=1, max_tool_rounds=3,
                  results_dir=str(root / 'results'), data_cache_dir=str(root / 'cache'),
                  memory_log_path=str(root / 'memory.md'))
    config['data_vendors']['fundamental_data'] = 'yfinance'
    return config


def start_analysis(ticker: str, as_of_date: str, portfolio: dict | None = None) -> dict:
    from tradingagents.portfolio import PortfolioContext
    book = PortfolioContext.model_validate(portfolio) if portfolio is not None else None
    global _running
    with _lock:
        if _running:
            raise ValueError('One model analysis is already running; wait for completion')
        _running = True
        job_id = str(uuid.uuid4())
        _jobs[job_id] = {'job_id': job_id, 'status': 'running', 'ticker': ticker,
                         'as_of_date': as_of_date, 'started_at': datetime.now(timezone.utc).isoformat()}
    def worker():
        global _running
        try:
            from tradingagents.graph.trading_graph import TradingAgentsGraph
            graph = TradingAgentsGraph(config=model_config())
            state, decision = graph.propagate(ticker, as_of_date, portfolio=book)
            graph.save_reports(state, ticker)
            fields = ('market_report', 'sentiment_report', 'news_report', 'fundamentals_report',
                      'investment_plan', 'trader_investment_plan', 'final_trade_decision',
                      'investment_debate_state', 'risk_debate_state')
            result = {'status': 'complete', 'decision': decision,
                      'reports': {k: state.get(k) for k in fields},
                      'completed_at': datetime.now(timezone.utc).isoformat()}
        except Exception as exc:
            result = {'status': 'failed', 'error_type': type(exc).__name__,
                      'message': 'Check local Codex login, model access, usage limits and data availability. No trade executed.'}
        with _lock:
            _jobs[job_id].update(result)
            _running = False
    threading.Thread(target=worker, daemon=True).start()
    return {'job_id': job_id, 'status': 'running', 'note': 'Poll model_analysis_status; consumes signed-in Codex model allowance.'}


def analysis_status(job_id: str) -> dict:
    with _lock:
        if job_id not in _jobs:
            raise ValueError('Unknown job; jobs are held in memory and reset on server restart')
        return deepcopy(_jobs[job_id])
