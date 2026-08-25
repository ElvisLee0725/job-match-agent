"""Shared test doubles for mocking the Claude client. Not a test module itself."""

from types import SimpleNamespace

import app.llm.client as llm_client


class _FakeToolUseBlock:
    def __init__(self, name: str, input_: dict):
        self.type = "tool_use"
        self.name = name
        self.input = input_


class _FakeMessages:
    def __init__(self, content: list):
        self._content = content

    def create(self, **kwargs):
        return SimpleNamespace(content=self._content)


class _FakeClient:
    def __init__(self, content: list):
        self.messages = _FakeMessages(content)


def mock_claude_tool_response(monkeypatch, tool_input: dict, *, tool_name: str = "emit_result") -> None:
    """Make the next `structured_completion(...)` call return `tool_input` as if Claude had
    called the `emit_result` tool with it."""
    fake_client = _FakeClient([_FakeToolUseBlock(tool_name, tool_input)])
    monkeypatch.setattr(llm_client, "get_client", lambda: fake_client)


def mock_claude_no_tool_call(monkeypatch) -> None:
    """Make the next `structured_completion(...)` call raise, simulating Claude replying
    without calling the expected tool."""
    fake_client = _FakeClient([])
    monkeypatch.setattr(llm_client, "get_client", lambda: fake_client)
