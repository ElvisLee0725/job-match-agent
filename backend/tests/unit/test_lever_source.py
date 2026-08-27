import json
from pathlib import Path

import httpx
import pytest
import respx

from app.sources.lever import LeverJobSource

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@respx.mock
def test_search_filters_by_keyword_and_maps_fields():
    fixture = json.loads((FIXTURES / "lever_postings_response.json").read_text())
    respx.get("https://api.lever.co/v0/postings/example").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    postings = LeverJobSource("example").search("backend software engineer", limit=10)

    assert len(postings) == 1
    posting = postings[0]
    assert posting.title == "Senior Backend Software Engineer"
    assert posting.company == "example"
    assert posting.location == "New York"
    assert posting.source_url == "https://jobs.lever.co/example/b1111111"
    assert "distributed backend systems" in posting.raw_description


@respx.mock
def test_search_raises_on_nonexistent_company():
    # Registry probes for existence before ever constructing a source, so this is an
    # edge case (e.g. a slug removed between probe and search) — propagate rather than
    # silently return no results, matching Oracle/Greenhouse's error handling.
    respx.get("https://api.lever.co/v0/postings/nonexistent").mock(
        return_value=httpx.Response(404, json={"ok": False, "error": "Document not found"})
    )

    with pytest.raises(httpx.HTTPStatusError):
        LeverJobSource("nonexistent").search("engineer")


@respx.mock
def test_fetch_full_description():
    respx.get("https://api.lever.co/v0/postings/example/b1111111").mock(
        return_value=httpx.Response(
            200, json={"descriptionPlain": "Full description of the backend role."}
        )
    )

    description = LeverJobSource("example").fetch_full_description("b1111111")

    assert description == "Full description of the backend role."
