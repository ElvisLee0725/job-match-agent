import re

import httpx

from app.sources.base import JobSource
from app.sources.greenhouse import GreenhouseJobSource
from app.sources.lever import LeverJobSource
from app.sources.oracle import OracleJobSource

_resolved_cache: dict[str, JobSource] = {}


class UnsupportedCompanyError(ValueError):
    pass


def _normalize(company_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", company_name.strip().lower())


def _probe(url: str, *, client: httpx.Client) -> bool:
    try:
        response = client.get(url, timeout=10.0)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def _probe_greenhouse(slug: str, *, client: httpx.Client) -> bool:
    return _probe(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", client=client)


def _probe_lever(slug: str, *, client: httpx.Client) -> bool:
    return _probe(f"https://api.lever.co/v0/postings/{slug}?mode=json", client=client)


def get_source(company_name: str) -> JobSource:
    key = _normalize(company_name)
    if not key:
        raise UnsupportedCompanyError("Company name can't be empty.")

    if key == "oracle":
        return OracleJobSource()

    if key in _resolved_cache:
        return _resolved_cache[key]

    with httpx.Client() as probe_client:
        if _probe_greenhouse(key, client=probe_client):
            source: JobSource = GreenhouseJobSource(key)
        elif _probe_lever(key, client=probe_client):
            source = LeverJobSource(key)
        else:
            raise UnsupportedCompanyError(
                f"Couldn't find '{company_name}' on Oracle, Greenhouse, or Lever. Try the "
                "exact company name as it appears in their job board URL, or paste a "
                "specific job posting URL instead."
            )

    _resolved_cache[key] = source
    return source
