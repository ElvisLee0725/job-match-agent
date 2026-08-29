def passes_title_filter(title: str, excluded_keywords: list[str]) -> bool:
    """Hard title filter applied before ranking, not left to LLM judgment.

    A posting is excluded if its title contains ANY excluded keyword
    (case-insensitive substring match). Mirrors `location_filter.passes_location_filter`
    — this exists because seniority-ceiling guidance in the matching prompt (see
    services/matching.py) is a soft instruction the model doesn't always follow
    (e.g. still occasionally surfacing "Principal" titles for a candidate who
    explicitly doesn't want them); an exact keyword exclusion is a hard guarantee.
    """
    if not excluded_keywords:
        return True

    title_lower = title.lower()
    return not any(
        keyword.strip().lower() in title_lower for keyword in excluded_keywords if keyword.strip()
    )
