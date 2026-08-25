from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import JobPosting, Profile
from app.models.job import JobPostingResponse, JobStructuredData, ParsedJobPosting
from app.models.profile import StructuredProfile
from app.services.job_structurer import structure_job_posting
from app.services.search_query import derive_search_query
from app.sources.registry import UnsupportedCompanyError, get_source
from app.sources.url_parser import SingleUrlJobParser

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class ScrapeRequest(BaseModel):
    company_name: str
    query: str | None = None
    limit: int = 100


class ParseUrlRequest(BaseModel):
    url: str
    company: str = "unknown"


def _to_response(posting: JobPosting) -> JobPostingResponse:
    return JobPostingResponse(
        id=posting.id,
        company=posting.company,
        source_type=posting.source_type,
        source_url=posting.source_url,
        external_id=posting.external_id,
        title=posting.title,
        location=posting.location,
        raw_description=posting.raw_description,
        structured=JobStructuredData.model_validate_json(posting.structured_json),
        scraped_at=posting.scraped_at,
    )


def _upsert(db: Session, parsed: ParsedJobPosting) -> JobPosting:
    existing = db.query(JobPosting).filter_by(source_url=parsed.source_url).first()
    if existing is None:
        existing = JobPosting(company=parsed.company, source_url=parsed.source_url)
        db.add(existing)

    existing.company = parsed.company
    existing.source_type = parsed.source_type
    existing.external_id = parsed.external_id
    existing.title = parsed.title
    existing.location = parsed.location
    existing.raw_description = parsed.raw_description
    return existing


@router.post("/scrape", response_model=list[JobPostingResponse])
def scrape_jobs(payload: ScrapeRequest, db: Session = Depends(get_db)) -> list[JobPostingResponse]:
    try:
        source = get_source(payload.company_name)
    except UnsupportedCompanyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    query = payload.query
    if not query:
        profile = db.query(Profile).first()
        if profile is None:
            raise HTTPException(
                status_code=400,
                detail="No search query given and no profile is stored yet — upload a "
                "profile first, or pass an explicit `query`.",
            )
        structured = StructuredProfile.model_validate_json(profile.structured_json)
        query = derive_search_query(structured)

    parsed_postings = source.search(query, limit=payload.limit)

    saved = [_upsert(db, parsed) for parsed in parsed_postings]
    db.commit()
    for posting in saved:
        db.refresh(posting)

    return [_to_response(posting) for posting in saved]


@router.get("", response_model=list[JobPostingResponse])
def list_jobs(company: str, db: Session = Depends(get_db)) -> list[JobPostingResponse]:
    postings = db.query(JobPosting).filter_by(company=company.strip().lower()).all()
    return [_to_response(posting) for posting in postings]


@router.post("/parse-url", response_model=JobPostingResponse)
def parse_job_url(payload: ParseUrlRequest, db: Session = Depends(get_db)) -> JobPostingResponse:
    parser = SingleUrlJobParser()
    try:
        parsed = parser.parse(payload.url, payload.company.strip().lower())
    except Exception as exc:  # noqa: BLE001 - surface any fetch/parse failure as a 502
        raise HTTPException(status_code=502, detail=f"Could not parse that URL: {exc}") from exc

    posting = _upsert(db, parsed)
    # A pasted URL is a single posting, so structuring it now (one cheap Claude call) is
    # worth it — unlike bulk company search, which returns too many candidates to structure
    # individually at ingestion time.
    posting.structured_json = structure_job_posting(parsed.raw_description).model_dump_json()
    db.commit()
    db.refresh(posting)
    return _to_response(posting)
