import httpx
import pytest
import respx

from app.sources import registry
from app.sources.greenhouse import GreenhouseJobSource
from app.sources.lever import LeverJobSource
from app.sources.oracle import OracleJobSource
from app.sources.registry import UnsupportedCompanyError, get_source


@pytest.fixture(autouse=True)
def clear_registry_cache():
    registry._resolved_cache.clear()
    yield
    registry._resolved_cache.clear()


def test_oracle_is_resolved_without_probing():
    source = get_source("Oracle")
    assert isinstance(source, OracleJobSource)


@respx.mock
def test_resolves_to_greenhouse_when_board_exists():
    respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs").mock(
        return_value=httpx.Response(200, json={"jobs": []})
    )

    source = get_source("Stripe")

    assert isinstance(source, GreenhouseJobSource)


@respx.mock
def test_falls_back_to_lever_when_greenhouse_has_no_board():
    respx.get("https://boards-api.greenhouse.io/v1/boards/palantir/jobs").mock(
        return_value=httpx.Response(404, json={"status": 404, "error": "Job not found"})
    )
    respx.get("https://api.lever.co/v0/postings/palantir").mock(
        return_value=httpx.Response(200, json=[])
    )

    source = get_source("Palantir")

    assert isinstance(source, LeverJobSource)


@respx.mock
def test_raises_clear_error_when_neither_platform_has_the_company():
    respx.get("https://boards-api.greenhouse.io/v1/boards/meta/jobs").mock(
        return_value=httpx.Response(404, json={"status": 404, "error": "Job not found"})
    )
    respx.get("https://api.lever.co/v0/postings/meta").mock(
        return_value=httpx.Response(404, json={"ok": False, "error": "Document not found"})
    )

    with pytest.raises(UnsupportedCompanyError, match="paste"):
        get_source("Meta")


def test_empty_company_name_raises():
    with pytest.raises(UnsupportedCompanyError):
        get_source("   ")


@respx.mock
def test_normalizes_whitespace_case_and_punctuation_before_probing():
    route = respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs").mock(
        return_value=httpx.Response(200, json={"jobs": []})
    )

    get_source("  STRIPE!  ")

    assert route.called


@respx.mock
def test_second_lookup_uses_cache_and_does_not_reprobe():
    route = respx.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs").mock(
        return_value=httpx.Response(200, json={"jobs": []})
    )

    get_source("stripe")
    get_source("stripe")

    assert route.call_count == 1
