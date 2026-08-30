import re
from urllib.parse import quote

import httpx

from app.models.job import ParsedJobPosting
from app.sources.base import JobSource
from app.sources.html_utils import strip_html

_BASE_API_URL = "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest"
_SITE_NUMBER = "CX_45001"
_JOB_URL_TEMPLATE = "https://careers.oracle.com/en/sites/jobsearch/job/{id}"

# Matches both URL formats Oracle job postings show up in the wild: the public
# careers.oracle.com wrapper, and the underlying eeho.fa.us2.oraclecloud.com "Candidate
# Experience" app URL people often copy/share directly (e.g. from LinkedIn) — that one is a
# JS-rendered SPA a plain HTTP fetch can't read, which is exactly why detecting it and
# routing through this API instead matters (see SingleUrlJobParser).
_ORACLE_JOB_URL_PATTERN = re.compile(
    r"(?:careers\.oracle\.com|\.oraclecloud\.com)/.*?/jobsearch/job/(\d+)", re.IGNORECASE
)


def extract_oracle_job_id(url: str) -> str | None:
    match = _ORACLE_JOB_URL_PATTERN.search(url)
    return match.group(1) if match else None


def _sanitize_keyword(query: str) -> str:
    # `,` and `;` are the Oracle "finder" syntax's own delimiters — a literal one in the
    # search text would get parsed as part of the finder expression rather than the keyword.
    cleaned = re.sub(r"[,;]", " ", query)
    return re.sub(r"\s+", " ", cleaned).strip()


class OracleJobSource(JobSource):
    company_name = "oracle"

    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=15.0)

    def _finder_url(self, resource: str, finder: str, expand: str) -> str:
        encoded_finder = quote(finder, safe=";,=")
        return f"{_BASE_API_URL}/{resource}?onlyData=true&expand={expand}&finder={encoded_finder}"

    def search(self, query: str, limit: int = 100) -> list[ParsedJobPosting]:
        keyword = _sanitize_keyword(query)
        finder = f"findReqs;siteNumber={_SITE_NUMBER},limit={limit},offset=0,keyword={keyword}"
        url = self._finder_url("recruitingCEJobRequisitions", finder, expand="requisitionList")

        response = self._client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        requisitions = data["items"][0]["requisitionList"] if data.get("items") else []

        postings = []
        for req in requisitions:
            job_id = str(req["Id"])
            postings.append(
                ParsedJobPosting(
                    company=self.company_name,
                    source_type="scraped",
                    source_url=_JOB_URL_TEMPLATE.format(id=job_id),
                    external_id=job_id,
                    title=req.get("Title", ""),
                    location=req.get("PrimaryLocation"),
                    raw_description=strip_html(req.get("ShortDescriptionStr")),
                )
            )
        return postings

    def _fetch_detail_item(self, external_id: str) -> dict:
        finder = f'ById;Id="{external_id}",siteNumber={_SITE_NUMBER}'
        url = self._finder_url("recruitingCEJobRequisitionDetails", finder, expand="all")

        response = self._client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        if not data.get("items"):
            raise ValueError(f"No job details found for Oracle requisition id {external_id!r}")
        return data["items"][0]

    def fetch_full_description(self, external_id: str) -> str:
        item = self._fetch_detail_item(external_id)
        return strip_html(item.get("ExternalDescriptionStr"))

    def fetch_posting_by_id(self, external_id: str, source_url: str | None = None) -> ParsedJobPosting:
        """Fetch a single posting directly by its Oracle requisition id — used when a user
        pastes a specific Oracle job URL rather than searching."""
        item = self._fetch_detail_item(external_id)
        return ParsedJobPosting(
            company=self.company_name,
            source_type="scraped",
            source_url=source_url or _JOB_URL_TEMPLATE.format(id=external_id),
            external_id=external_id,
            title=item.get("Title", ""),
            location=item.get("PrimaryLocation"),
            raw_description=strip_html(item.get("ExternalDescriptionStr")),
        )
