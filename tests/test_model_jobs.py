from tradingagents.mcp_server import model_jobs


def test_job_runs_original_graph_and_reports(monkeypatch, tmp_path):
    import tradingagents.graph.trading_graph as graph_module
    monkeypatch.setenv('TRADINGAGENTS_MCP_DATA_DIR', str(tmp_path))
    calls = []
    class Graph:
        def __init__(self, config):
            assert config['llm_provider'] == 'codex'
        def propagate(self, ticker, day, portfolio=None):
            calls.append(('run', ticker, day))
            return {'final_trade_decision': 'Hold', 'market_report': 'dated evidence'}, 'Hold'
        def save_reports(self, state, ticker):
            calls.append(('save', ticker))
    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
        def start(self):
            self.target()
    monkeypatch.setattr(graph_module, 'TradingAgentsGraph', Graph)
    monkeypatch.setattr(model_jobs.threading, 'Thread', ImmediateThread)
    result = model_jobs.start_analysis('TCS.NS', '2026-10-09')
    completed = model_jobs.analysis_status(result['job_id'])
    assert completed['status'] == 'complete'
    assert completed['decision'] == 'Hold'
    assert calls == [('run', 'TCS.NS', '2026-10-09'), ('save', 'TCS.NS')]


def test_failed_job_does_not_claim_completed(monkeypatch):
    import tradingagents.graph.trading_graph as graph_module
    class Graph:
        def __init__(self, config):
            raise RuntimeError('private details')
    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
        def start(self):
            self.target()
    monkeypatch.setattr(graph_module, 'TradingAgentsGraph', Graph)
    monkeypatch.setattr(model_jobs.threading, 'Thread', ImmediateThread)
    result = model_jobs.start_analysis('TCS.NS', '2026-10-09')
    completed = model_jobs.analysis_status(result['job_id'])
    assert completed['status'] == 'failed'
    assert 'private details' not in str(completed)
