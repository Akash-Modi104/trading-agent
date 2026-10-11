import json
from types import SimpleNamespace
import pytest
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from tradingagents.llm_clients import codex_client
from tradingagents.llm_clients.factory import create_llm_client


def fake_cli(monkeypatch, payload, code=0):
    monkeypatch.setattr(codex_client.shutil, 'which', lambda exe: '/fake/codex')
    def run(command, **kwargs):
        assert '--ephemeral' in command and '--ignore-user-config' in command
        assert command[command.index('--sandbox')+1] == 'read-only'
        assert kwargs['input'] and 'shell' not in kwargs
        codex_client.Path(command[command.index('--output-last-message')+1]).write_text(json.dumps(payload))
        return SimpleNamespace(returncode=code)
    monkeypatch.setattr(codex_client.subprocess, 'run', run)


def test_plain_model_and_factory(monkeypatch):
    fake_cli(monkeypatch, {'content': 'evidence-based report', 'tool_calls': []})
    assert create_llm_client('codex', '').get_llm().invoke('analyse').content == 'evidence-based report'


def test_bound_tools(monkeypatch):
    tool={'type':'function','function':{'name':'lookup','description':'lookup', 'parameters':{'type':'object','properties':{}}}}
    fake_cli(monkeypatch, {'content':'', 'tool_calls':[{'name':'lookup','args':{}}]})
    result = codex_client.CodexChatModel().bind_tools([tool]).invoke([HumanMessage(content='lookup')])
    assert result.tool_calls[0]['name'] == 'lookup'


def test_reject_unknown_tool(monkeypatch):
    fake_cli(monkeypatch, {'content':'', 'tool_calls':[{'name':'place_order','args':{}}]})
    with pytest.raises(ValueError):
        codex_client.CodexChatModel().invoke('analyse')


def test_structured_output(monkeypatch):
    class Rating(BaseModel):
        rating: str
    fake_cli(monkeypatch, {'rating': 'Hold'})
    assert codex_client.CodexChatModel().with_structured_output(Rating).invoke('analyse').rating == 'Hold'


def test_failed_model_is_not_fake_report(monkeypatch):
    fake_cli(monkeypatch, {'content':'ignored'}, code=1)
    with pytest.raises(RuntimeError):
        codex_client.CodexChatModel().invoke('analyse')
