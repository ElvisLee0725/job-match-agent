import pytest

from app.models.profile import StructuredProfile
from app.services.profile_builder import build_structured_profile
from tests.unit._support import mock_claude_no_tool_call, mock_claude_tool_response


def test_build_structured_profile_parses_tool_response(monkeypatch):
    expected = {
        "skills": ["Python", "FastAPI"],
        "experience_years": 6.0,
        "seniority": "senior",
        "domains": ["fintech"],
        "summary": "Experienced backend engineer who leads migrations.",
    }
    mock_claude_tool_response(monkeypatch, expected)

    result = build_structured_profile("resume text", "background notes", ["answer one"])

    assert isinstance(result, StructuredProfile)
    assert result.skills == ["Python", "FastAPI"]
    assert result.experience_years == 6.0
    assert result.seniority == "senior"


def test_build_structured_profile_raises_when_no_tool_call_returned(monkeypatch):
    mock_claude_no_tool_call(monkeypatch)

    with pytest.raises(ValueError):
        build_structured_profile("resume text", "", [])
