from concurrent.futures import ThreadPoolExecutor

import httpx

from app.db.models import JobPosting
from app.sources.base import JobSource

_MAX_WORKERS = 10


def _is_live(posting: JobPosting, source: JobSource) -> bool:
    if not posting.external_id:
        # Can't verify a posting we have no external id for (e.g. a generic "paste a URL"
        # posting from a site with no API) — trust the cache rather than drop it.
        return True
    try:
        return source.check_exists(posting.external_id)
    except httpx.HTTPError:
        # A network hiccup shouldn't cost the user a posting that's probably still live —
        # fail open rather than silently dropping it.
        return True


def filter_still_live(postings: list[JobPosting], source: JobSource | None) -> list[JobPosting]:
    """Drop cached postings that no longer exist at the source before they're shown to the
    user. Cached postings can go stale days or weeks after being scraped (a company closes
    or fills the role), so trusting the cache indefinitely surfaces dead links."""
    if source is None or not postings:
        return postings

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        still_live = list(pool.map(lambda p: _is_live(p, source), postings))

    return [p for p, live in zip(postings, still_live) if live]
