import httpx

from app.models.job import ParsedJobPosting
from app.sources.base import JobSource
from app.sources.keyword_filter import filter_and_rank_by_keyword

_BASE_URL = "https://api.lever.co/v0/postings"


class LeverJobSource(JobSource):
    """Works for any company whose careers page is powered by Lever. Like Greenhouse,
    Lever's public API has no server-side keyword search, so filtering happens
    client-side (see `filter_and_rank_by_keyword`). Unlike Greenhouse, Lever's list
    endpoint already returns full plain-text descriptions, so no separate detail call is
    needed to populate `raw_description`."""

    def __init__(self, company_slug: str, client: httpx.Client | None = None):
        self.company_name = company_slug
        self._company_slug = company_slug
        self._client = client or httpx.Client(timeout=15.0)

    def _list_postings(self) -> list[dict]:
        response = self._client.get(f"{_BASE_URL}/{self._company_slug}", params={"mode": "json"})
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    def search(self, query: str, limit: int = 100) -> list[ParsedJobPosting]:
        postings_raw = self._list_postings()
        selected = filter_and_rank_by_keyword(
            postings_raw, query, get_title=lambda p: p.get("text", ""), limit=limit
        )

        postings = []
        for posting in selected:
            categories = posting.get("categories") or {}
            postings.append(
                ParsedJobPosting(
                    company=self.company_name,
                    source_type="scraped",
                    source_url=posting.get("hostedUrl", ""),
                    external_id=posting.get("id"),
                    title=posting.get("text", ""),
                    location=categories.get("location"),
                    raw_description=posting.get("descriptionPlain", ""),
                )
            )
        return postings

    def fetch_full_description(self, external_id: str) -> str:
        response = self._client.get(
            f"{_BASE_URL}/{self._company_slug}/{external_id}", params={"mode": "json"}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("descriptionPlain", "")
