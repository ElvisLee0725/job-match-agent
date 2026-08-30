import re

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.llm.client import structured_completion
from app.models.job import ParsedJobPosting
from app.sources.oracle import OracleJobSource, extract_oracle_job_id

_PROMPT_TEMPLATE = """\
Below is the extracted text of a single job posting web page. Pull out the job title, the \
work location if mentioned (or null if not mentioned), and the full job description text \
(responsibilities, requirements, qualifications — everything relevant to evaluating fit, \
cleaned of navigation/footer/unrelated site chrome).

Page text:
---
{page_text}
---
"""


class _ExtractedJobPage(BaseModel):
    title: str
    location: str | None = None
    description: str


_MIN_PAGE_TEXT_LENGTH = 200


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()


class SingleUrlJobParser:
    """Fetches exactly one job posting URL a user explicitly provides (e.g. a LinkedIn link
    they're looking at) and parses it into a ParsedJobPosting. Deliberately not a JobSource:
    this is single-page, user-directed fetching, not automated company-wide scraping."""

    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; job-match-agent personal tool)"},
        )

    def parse(self, url: str, company: str) -> ParsedJobPosting:
        # Oracle job links (either their public careers.oracle.com wrapper, or the
        # underlying eeho.fa.us2.oraclecloud.com "Candidate Experience" URL people often
        # copy/share directly) are JS-rendered SPAs a plain HTML fetch can't read. Since we
        # already have a real API integration for Oracle, route these through it instead of
        # the generic fetch-and-ask-Claude path — more reliable and doesn't need an LLM call.
        oracle_job_id = extract_oracle_job_id(url)
        if oracle_job_id:
            return OracleJobSource().fetch_posting_by_id(oracle_job_id, source_url=url)

        response = self._client.get(url)
        response.raise_for_status()

        page_text = BeautifulSoup(response.text, "lxml").get_text(separator="\n")
        cleaned = _collapse_whitespace(page_text)[:15000]

        if len(cleaned) < _MIN_PAGE_TEXT_LENGTH:
            raise ValueError(
                "This page returned almost no readable text, which usually means it's "
                "rendered by JavaScript and can't be fetched as plain HTML. Try copying the "
                "job description text directly instead, or use a different posting link."
            )

        extracted = structured_completion(
            _PROMPT_TEMPLATE.format(page_text=cleaned), _ExtractedJobPage
        )

        return ParsedJobPosting(
            company=company,
            source_type="manual_url",
            source_url=url,
            external_id=None,
            title=extracted.title,
            location=extracted.location,
            raw_description=extracted.description,
        )
