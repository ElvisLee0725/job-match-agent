import json
from pathlib import Path

import httpx
import pytest
import respx

from app.sources.url_parser import SingleUrlJobParser
from tests.unit._support import mock_claude_tool_response

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
ORACLE_DETAIL_URL_RE = r"https://eeho\.fa\.us2\.oraclecloud\.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails.*"

_REALISTIC_JOB_HTML = """
<html><body>
<h1>Backend Engineer</h1>
<p>We are looking for a Backend Engineer to join our platform team. You will design,
build, and operate scalable APIs and services, collaborate closely with product and
data teams, and help shape our technical roadmap. Requirements: 3+ years of experience
with Python or Java, familiarity with cloud infrastructure, and strong communication
skills. This is a remote-friendly role with a collaborative, fast-paced culture.</p>
</body></html>
"""


@respx.mock
def test_parse_fetches_page_and_returns_parsed_posting(monkeypatch):
    respx.get("https://example.com/job/123").mock(
        return_value=httpx.Response(200, html=_REALISTIC_JOB_HTML)
    )
    mock_claude_tool_response(
        monkeypatch,
        {
            "title": "Backend Engineer",
            "location": "Remote",
            "description": "Build and maintain backend services.",
        },
    )

    posting = SingleUrlJobParser().parse("https://example.com/job/123", company="acme")

    assert posting.company == "acme"
    assert posting.source_type == "manual_url"
    assert posting.source_url == "https://example.com/job/123"
    assert posting.title == "Backend Engineer"
    assert posting.location == "Remote"
    assert posting.external_id is None


@respx.mock
def test_parse_raises_clear_error_for_js_rendered_page_with_no_text(monkeypatch):
    # Simulates a JS-rendered SPA page (e.g. Oracle's own career site) where a plain HTTP
    # fetch returns almost no text content — we should fail clearly instead of asking
    # Claude to hallucinate a posting from near-nothing.
    respx.get("https://example.com/job/456").mock(
        return_value=httpx.Response(200, html="<html><head><title>App</title></head><body></body></html>")
    )

    with pytest.raises(ValueError, match="JavaScript"):
        SingleUrlJobParser().parse("https://example.com/job/456", company="acme")


@respx.mock
def test_parse_routes_oracle_candidate_experience_url_through_oracle_api_directly():
    # This is the exact bug report: a real Oracle "Candidate Experience" URL (e.g. shared
    # via LinkedIn) is a JS-rendered SPA a plain fetch can't read. It must be detected and
    # routed through OracleJobSource's real API instead of the generic HTML+LLM path —
    # confirmed by NOT mocking the generic page URL at all: if the code fell through to the
    # generic path, this test would fail with a connection error, not a wrong assertion.
    fixture = json.loads((FIXTURES / "oracle_detail_response.json").read_text())
    respx.get(url__regex=ORACLE_DETAIL_URL_RE).mock(return_value=httpx.Response(200, json=fixture))

    url = (
        "https://eeho.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/jobsearch/"
        "job/333297?utm_medium=jobboard&utm_source=LinkedIn"
    )
    posting = SingleUrlJobParser().parse(url, company="ignored")

    assert posting.company == "oracle"  # overridden regardless of the passed-in company
    assert posting.source_type == "scraped"
    assert posting.external_id == "333297"
    assert posting.source_url == url  # preserves the exact URL the user pasted
    assert posting.title
    assert "<p>" not in posting.raw_description
