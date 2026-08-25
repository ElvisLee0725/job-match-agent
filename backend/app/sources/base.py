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
