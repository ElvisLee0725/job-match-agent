import json
from pathlib import Path
from urllib.parse import unquote

import httpx
import respx

from app.sources.oracle import OracleJobSource, extract_oracle_job_id

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SEARCH_URL_RE = r"https://eeho\.fa\.us2\.oraclecloud\.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions.*"
DETAIL_URL_RE = r"https://eeho\.fa\.us2\.oraclecloud\.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails.*"


@respx.mock
def test_search_parses_requisitions_into_parsed_job_postings():
    fixture = json.loads((FIXTURES / "oracle_search_response.json").read_text())
    respx.get(url__regex=SEARCH_URL_RE).mock(return_value=httpx.Response(200, json=fixture))

    postings = OracleJobSource().search("Python Backend Engineer", limit=5)

    assert len(postings) == 5
    first = postings[0]
    assert first.company == "oracle"
    assert first.source_type == "scraped"
    assert first.source_url.startswith("https://careers.oracle.com/en/sites/jobsearch/job/")
    assert first.external_id
    assert first.title


@respx.mock
def test_search_sanitizes_delimiter_characters_in_keyword():
    route = respx.get(url__regex=SEARCH_URL_RE).mock(
        return_value=httpx.Response(200, json={"items": []})
    )

    OracleJobSource().search("Python, Backend; Engineer")

    sent_url = unquote(str(route.calls[0].request.url))
    assert "keyword=Python Backend Engineer" in sent_url


@respx.mock
def test_search_returns_empty_list_when_no_results():
    respx.get(url__regex=SEARCH_URL_RE).mock(return_value=httpx.Response(200, json={"items": []}))

    assert OracleJobSource().search("some very obscure query") == []


@respx.mock
def test_fetch_full_description_returns_cleaned_text_from_detail_fixture():
    fixture = json.loads((FIXTURES / "oracle_detail_response.json").read_text())
    respx.get(url__regex=DETAIL_URL_RE).mock(return_value=httpx.Response(200, json=fixture))

    description = OracleJobSource().fetch_full_description("333297")

    assert len(description) > 100
    assert "<p>" not in description  # HTML stripped


@respx.mock
def test_fetch_posting_by_id_returns_full_parsed_posting():
    fixture = json.loads((FIXTURES / "oracle_detail_response.json").read_text())
    respx.get(url__regex=DETAIL_URL_RE).mock(return_value=httpx.Response(200, json=fixture))

    posting = OracleJobSource().fetch_posting_by_id(
        "333297", source_url="https://careers.oracle.com/en/sites/jobsearch/job/333297"
    )

    assert posting.company == "oracle"
    assert posting.source_type == "scraped"
    assert posting.external_id == "333297"
    assert posting.source_url == "https://careers.oracle.com/en/sites/jobsearch/job/333297"
    assert posting.title
    assert "<p>" not in posting.raw_description


def test_extract_oracle_job_id_matches_public_careers_url():
    assert (
        extract_oracle_job_id("https://careers.oracle.com/en/sites/jobsearch/job/334575")
        == "334575"
    )


def test_extract_oracle_job_id_matches_candidate_experience_url_with_query_params():
    url = (
        "https://eeho.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/jobsearch/"
        "job/334575?utm_medium=jobboard&utm_source=LinkedIn"
    )
    assert extract_oracle_job_id(url) == "334575"


def test_extract_oracle_job_id_returns_none_for_non_oracle_url():
    assert extract_oracle_job_id("https://www.linkedin.com/jobs/view/12345") is None
