from app.models.job import JobStructuredData
from app.services.job_structurer import structure_job_posting
from tests.unit._support import mock_claude_tool_response


def test_structure_job_posting_parses_tool_response(monkeypatch):
    expected = {
        "requirements": ["Python", "5+ years experience"],
        "responsibilities": ["Design APIs", "Mentor engineers"],
        "seniority": "senior",
        "domain": "cloud infrastructure",
    }
    mock_claude_tool_response(monkeypatch, expected)

    result = structure_job_posting("Some raw job description text.")

    assert isinstance(result, JobStructuredData)
    assert result.seniority == "senior"
    assert result.requirements == ["Python", "5+ years experience"]
