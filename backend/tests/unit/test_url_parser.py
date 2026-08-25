import httpx
import pytest
import respx

from app.sources.url_parser import SingleUrlJobParser
from tests.unit._support import mock_claude_tool_response

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
