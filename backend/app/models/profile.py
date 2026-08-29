from datetime import datetime

from pydantic import BaseModel


class StructuredProfile(BaseModel):
    skills: list[str] = []
    experience_years: float = 0.0
    seniority: str = ""
    domains: list[str] = []
    summary: str = ""


class ProfileResponse(BaseModel):
    id: int
    raw_resume_text: str
    background_text: str
    behavioral_answers: list[str]
    structured_profile: StructuredProfile
    us_only: bool
    preferred_states: list[str]
    excluded_title_keywords: list[str]
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    background_text: str | None = None
    behavioral_answers: list[str] | None = None
    us_only: bool | None = None
    preferred_states: list[str] | None = None
    excluded_title_keywords: list[str] | None = None
