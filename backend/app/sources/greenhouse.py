import httpx

from app.models.job import ParsedJobPosting
from app.sources.base import JobSource
from app.sources.html_utils import strip_html
from app.sources.keyword_filter import filter_and_rank_by_keyword

_BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseJobSource(JobSource):
    """Works for any company whose careers page is powered by Greenhouse — the platform
    has no server-side keyword search, so filtering happens client-side after fetching
    the whole board (see `filter_and_rank_by_keyword`)."""

    def __init__(self, board_token: str, client: httpx.Client | None = None):
        self.company_name = board_token
        self._board_token = board_token
        self._client = client or httpx.Client(timeout=15.0)

    def _list_jobs(self) -> list[dict]:
        response = self._client.get(f"{_BASE_URL}/{self._board_token}/jobs")
        response.raise_for_status()
        return response.json().get("jobs", [])

    def search(self, query: str, limit: int = 100) -> list[ParsedJobPosting]:
        jobs = self._list_jobs()
        selected = filter_and_rank_by_keyword(
            jobs, query, get_title=lambda j: j.get("title", ""), limit=limit
        )

        postings = []
        for job in selected:
            job_id = str(job["id"])
            location = job.get("location") or {}
            postings.append(
                ParsedJobPosting(
                    company=self.company_name,
                    source_type="scraped",
                    source_url=job.get("absolute_url", ""),
                    external_id=job_id,
                    title=job.get("title", ""),
                    location=location.get("name"),
                    raw_description="",
                )
            )
        return postings

    def fetch_full_description(self, external_id: str) -> str:
        url = f"{_BASE_URL}/{self._board_token}/jobs/{external_id}?content=true"
        response = self._client.get(url)
        response.raise_for_status()
        data = response.json()
        return strip_html(data.get("content"))
