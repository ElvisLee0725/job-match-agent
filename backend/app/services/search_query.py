from app.models.profile import StructuredProfile


def derive_search_query(profile: StructuredProfile, max_skills: int = 2) -> str:
    """Build a job-search keyword string from a structured candidate profile.

    Deterministic (no LLM call) — cheap to run and easy to test, and it just needs to be
    good enough to hand to the target company's own search/relevancy ranking, not perfect.

    Kept deliberately short: testing against Oracle's real search API showed queries beyond
    ~4-5 words (e.g. seniority + 4 skills + a domain phrase) reliably return zero results,
    likely because the search ANDs terms together and over-specific combinations have no
    matches. Seniority + top 2 skills stays comfortably inside the range that works, and the
    target company's own relevancy ranking does the rest of the narrowing. Domain is
    deliberately omitted — multi-word domain phrases (e.g. "real estate/property data") are
    often about the candidate's *previous* industry, not relevant to what they're searching
    for now, and were a major contributor to zero-result queries in testing.
    """
    parts: list[str] = []
    if profile.seniority:
        parts.append(profile.seniority)
    parts.extend(profile.skills[:max_skills])
    return " ".join(parts).strip()
