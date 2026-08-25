from app.models.profile import StructuredProfile
from app.services.search_query import derive_search_query


def test_derive_search_query_combines_seniority_and_top_skills():
    profile = StructuredProfile(
        skills=["Python", "FastAPI", "AWS", "Kubernetes", "Terraform"],
        experience_years=6.0,
        seniority="senior",
        domains=["fintech", "cloud infrastructure"],
        summary="",
    )

    query = derive_search_query(profile)

    # short by design (kept to seniority + 2 skills, no domain) — long queries reliably
    # returned zero results against Oracle's real search API
    assert query == "senior Python FastAPI"


def test_derive_search_query_handles_missing_fields():
    profile = StructuredProfile(skills=[], experience_years=0.0, seniority="", domains=[], summary="")

    assert derive_search_query(profile) == ""
