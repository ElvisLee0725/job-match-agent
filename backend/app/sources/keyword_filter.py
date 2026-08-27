import re
from typing import Callable, TypeVar

T = TypeVar("T")


def keyword_match_score(title: str, query: str) -> int:
    """Count how many distinct query words appear in title (case-insensitive)."""
    words = {w for w in re.findall(r"\w+", query.lower()) if w}
    title_lower = title.lower()
    return sum(1 for w in words if w in title_lower)


def filter_and_rank_by_keyword(
    items: list[T], query: str, get_title: Callable[[T], str], limit: int
) -> list[T]:
    """Client-side keyword filter + rank, for platforms (Greenhouse, Lever) whose public
    APIs return an entire job board with no server-side search — unlike Oracle, which
    filters server-side via its own search API."""
    scored = [(keyword_match_score(get_title(item), query), item) for item in items]
    matched = [(score, item) for score, item in scored if score > 0]
    matched.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in matched[:limit]]
