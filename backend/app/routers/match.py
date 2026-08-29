import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobPosting, MatchResult, Profile
from app.models.match import MatchPickResponse, MatchRunRequest, MatchRunResponse
from app.models.profile import StructuredProfile
from app.services.location_filter import passes_location_filter
from app.services.matching import JobCandidate, rank_top_matches
from app.services.title_filter import passes_title_filter

router = APIRouter(prefix="/api/match", tags=["match"])


@router.post("/run", response_model=MatchRunResponse)
def run_match(payload: MatchRunRequest, db: Session = Depends(get_db)) -> MatchRunResponse:
    company = payload.company_name.strip().lower()

    profile = db.query(Profile).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile has been uploaded yet.")

    all_postings = db.query(JobPosting).filter_by(company=company).all()
    if not all_postings:
        raise HTTPException(
            status_code=400,
            detail=f"No cached postings for '{company}' — run /api/jobs/scrape first.",
        )

    preferred_states = json.loads(profile.preferred_states_json)
    excluded_title_keywords = json.loads(profile.excluded_title_keywords_json)
    postings = [
        p
        for p in all_postings
        if passes_location_filter(
            p.location, us_only=profile.us_only, preferred_states=preferred_states
        )
        and passes_title_filter(p.title, excluded_title_keywords)
    ]
    if not postings:
        raise HTTPException(
            status_code=400,
            detail=f"None of the {len(all_postings)} cached postings for '{company}' match "
            "your location and title preferences — try broadening them or searching again.",
        )

    structured_profile = StructuredProfile.model_validate_json(profile.structured_json)
    postings_by_id = {p.id: p for p in postings}
    candidates = [
        JobCandidate(
            job_posting_id=p.id,
            title=p.title,
            location=p.location,
            description_snippet=p.raw_description,
        )
        for p in postings
    ]

    picks = rank_top_matches(structured_profile, candidates, top_n=payload.top_n)

    results = [
        MatchPickResponse(
            job_posting_id=pick.job_posting_id,
            rank=pick.rank,
            fit_score=pick.fit_score,
            rationale=pick.rationale,
            title=postings_by_id[pick.job_posting_id].title,
            company=postings_by_id[pick.job_posting_id].company,
            location=postings_by_id[pick.job_posting_id].location,
            source_url=postings_by_id[pick.job_posting_id].source_url,
        )
        for pick in picks
    ]

    match_result = MatchResult(
        profile_id=profile.id,
        company=company,
        results_json=json.dumps([r.model_dump(mode="json") for r in results]),
    )
    db.add(match_result)
    db.commit()
    db.refresh(match_result)

    return MatchRunResponse(
        match_run_id=match_result.id,
        company=match_result.company,
        run_at=match_result.run_at,
        results=results,
    )


@router.get("/latest", response_model=MatchRunResponse)
def get_latest_match(company: str, db: Session = Depends(get_db)) -> MatchRunResponse:
    match_result = (
        db.query(MatchResult)
        .filter_by(company=company.strip().lower())
        .order_by(MatchResult.run_at.desc())
        .first()
    )
    if match_result is None:
        raise HTTPException(status_code=404, detail=f"No match runs found for '{company}' yet.")

    results = [MatchPickResponse.model_validate(r) for r in json.loads(match_result.results_json)]
    return MatchRunResponse(
        match_run_id=match_result.id,
        company=match_result.company,
        run_at=match_result.run_at,
        results=results,
    )
