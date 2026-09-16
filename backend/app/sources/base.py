from abc import ABC, abstractmethod

from app.models.job import ParsedJobPosting


class JobSource(ABC):
    """A company-specific job search backend.

    Implementations talk to whatever a company actually exposes (a JSON API, in Oracle's
    case) and normalize results into the shared `ParsedJobPosting` shape so downstream code
    (caching, matching) doesn't need to know which company/backend a posting came from.
    """

    company_name: str

    @abstractmethod
    def search(self, query: str, limit: int = 100) -> list[ParsedJobPosting]:
        """Return postings relevant to `query`, best-relevancy-first, capped at `limit`."""

    @abstractmethod
    def fetch_full_description(self, external_id: str) -> str:
        """Fetch the full job description text for one posting by its external id.

        Used to enrich only the final shortlisted postings, since search results only
        carry a short snippet.
        """

    @abstractmethod
    def check_exists(self, external_id: str) -> bool:
        """Return whether a posting is still live at the source, by its external id.

        Cached postings can go stale — a company closes or fills a role days or weeks
        after we scraped it — so this is used to filter cached candidates right before
        matching, rather than trusting the cache indefinitely.
        """
