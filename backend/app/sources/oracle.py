import re
from urllib.parse import quote

import httpx

from app.models.job import ParsedJobPosting
from app.sources.base import JobSource
from app.sources.html_utils import strip_html

_BASE_API_URL = "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest"
_SITE_NUMBER = "CX_45001"
_JOB_URL_TEMPLATE = "https://careers.oracle.com/en/sites/jobsearch/job/{id}"


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

    def fetch_full_description(self, external_id: str) -> str:
        finder = f'ById;Id="{external_id}",siteNumber={_SITE_NUMBER}'
        url = self._finder_url("recruitingCEJobRequisitionDetails", finder, expand="all")

        response = self._client.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        if not data.get("items"):
            raise ValueError(f"No job details found for Oracle requisition id {external_id!r}")
        return strip_html(data["items"][0].get("ExternalDescriptionStr"))
