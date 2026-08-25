from datetime import datetime

from pydantic import BaseModel


class MatchPickResponse(BaseModel):
    job_posting_id: int
    rank: int
    fit_score: int
    rationale: str
    title: str
    company: str
    location: str | None
    source_url: str


class MatchRunResponse(BaseModel):
    match_run_id: int
    company: str
    run_at: datetime
    results: list[MatchPickResponse]


class MatchRunRequest(BaseModel):
    company_name: str
    top_n: int = 3
