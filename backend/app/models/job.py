from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ParsedJobPosting(BaseModel):
    company: str
    source_type: Literal["scraped", "manual_url"]
    source_url: str
    external_id: str | None = None
    title: str
    location: str | None = None
    raw_description: str


class JobStructuredData(BaseModel):
    requirements: list[str] = []
    responsibilities: list[str] = []
    seniority: str = ""
    domain: str = ""


class JobPostingResponse(BaseModel):
    id: int
    company: str
    source_type: Literal["scraped", "manual_url"]
    source_url: str
    external_id: str | None
    title: str
    location: str | None
    raw_description: str
    structured: JobStructuredData
    scraped_at: datetime
