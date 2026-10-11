import asyncio
import pytest
from tradingagents.mcp_server import server


def test_validation():
    assert server.validate(' tcs.ns ', '2025-01-02') == ('TCS.NS', '2025-01-02')
    for symbol, day in [('https://bad', '2025-01-02'), ('TCS.NS', '2999-01-01'), ('TCS.NS', 'bad')]:
        with pytest.raises(ValueError):
            server.validate(symbol, day)


def test_failure_is_explicit_and_sanitized(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('secret private path')
    monkeypatch.setattr(server, 'build_verified_market_snapshot', fail)
    result = server.research_section('TCS.NS', '2025-01-02')
    assert result['status'] == 'unavailable'
    assert result['content'] is None
    assert 'secret' not in str(result)


def test_partial_packet(monkeypatch):
    monkeypatch.setattr(server, 'fetch_section', lambda t, d, s: {'status': 'unavailable' if s == 'news' else 'returned', 'content': s})
    result = server.research_packet('TCS.NS', '2025-01-02')
    assert len(result['sections']) == 6
    assert result['sections']['news']['status'] == 'unavailable'
    assert result['sections']['market']['status'] == 'returned'


def test_batches_reject_duplicates_and_excess():
    with pytest.raises(ValueError):
        server.screen_batch(['TCS.NS', 'tcs.ns'], '2025-01-02')
    with pytest.raises(ValueError):
        server.screen_batch(['TCS.NS'] * 11, '2025-01-02')


def test_mcp_discovery_no_trade_tools():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {'research_section', 'research_packet', 'screen_batch'}
    assert all(t.annotations.readOnlyHint for t in tools)
    assert len(asyncio.run(server.mcp.list_prompts())) == 1
