import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import respx

from app.sources.greenhouse import GreenhouseJobSource

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@respx.mock
def test_search_filters_by_keyword_and_maps_fields():
    fixture = json.loads((FIXTURES / "greenhouse_jobs_response.json").read_text())
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    postings = GreenhouseJobSource("stripe").search("backend engineer", limit=10)

    assert len(postings) == 1
    posting = postings[0]
    assert posting.title == "Senior Backend Engineer, Payments"
    assert posting.company == "stripe"
    assert posting.source_type == "scraped"
    assert posting.external_id == "7500001"
    assert posting.location == "Remote - US"
    assert posting.source_url == "https://stripe.com/jobs/search?gh_jid=7500001"
    assert posting.posted_at == datetime(2026, 7, 28, 5, 0, 0, tzinfo=timezone.utc)


@respx.mock
def test_search_respects_limit():
    fixture = json.loads((FIXTURES / "greenhouse_jobs_response.json").read_text())
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    postings = GreenhouseJobSource("stripe").search("engineer scientist", limit=1)

    assert len(postings) == 1


@respx.mock
def test_fetch_full_description_strips_html():
    fixture = json.loads((FIXTURES / "greenhouse_job_detail_response.json").read_text())
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs/7500001").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    description = GreenhouseJobSource("stripe").fetch_full_description("7500001")

    assert "<p>" not in description
    assert "Senior Backend Engineer" in description


@respx.mock
def test_check_exists_returns_true_for_200_response():
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs/7500001").mock(
        return_value=httpx.Response(200, json={"id": 7500001})
    )

    assert GreenhouseJobSource("stripe").check_exists("7500001") is True


@respx.mock
def test_check_exists_returns_false_for_404_response():
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs/999999").mock(
        return_value=httpx.Response(404)
    )

    assert GreenhouseJobSource("stripe").check_exists("999999") is False
