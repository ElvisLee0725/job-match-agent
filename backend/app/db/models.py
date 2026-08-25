from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_resume_text: Mapped[str] = mapped_column(Text, default="")
    background_text: Mapped[str] = mapped_column(Text, default="")
    behavioral_answers_json: Mapped[str] = mapped_column(Text, default="[]")
    structured_json: Mapped[str] = mapped_column(Text, default="{}")
    us_only: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_states_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(128), index=True)
    source_type: Mapped[str] = mapped_column(String(32))  # "scraped" | "manual_url"
    source_url: Mapped[str] = mapped_column(String(1024), unique=True)
    external_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, default="")
    structured_json: Mapped[str] = mapped_column(Text, default="{}")
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class MatchResult(Base):
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    company: Mapped[str] = mapped_column(String(128), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    results_json: Mapped[str] = mapped_column(Text, default="[]")
