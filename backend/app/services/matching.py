from pydantic import BaseModel

from app.llm.client import structured_completion
from app.models.profile import StructuredProfile

_SNIPPET_LENGTH = 600


class JobCandidate(BaseModel):
    job_posting_id: int
    title: str
    location: str | None
    description_snippet: str


class MatchPick(BaseModel):
    job_posting_id: int
    rank: int
    fit_score: int
    rationale: str


class _MatchRunOutput(BaseModel):
    picks: list[MatchPick]


_PROMPT_TEMPLATE = """\
You are helping a job candidate find the best-fitting open roles at a company from a list \
of candidate postings.

Candidate profile:
- Seniority: {seniority}
- Years of experience: {experience_years}
- Skills: {skills}
- Domains: {domains}
- Summary: {summary}

Open postings (each has a job_posting_id you must use to reference it):
{candidate_list}

Seniority ceiling: the candidate's level is "{seniority}". Only consider postings at that \
level or, at most, ONE level above it (e.g. if the candidate is Senior, Staff/Principal-type \
titles are acceptable). Do NOT pick postings that are two or more levels above the \
candidate's level (e.g. "Lead Principal", "Distinguished", "Director", "VP", or similarly \
senior-sounding titles beyond one step up) even if the skills otherwise match well — treat \
that seniority gap as disqualifying, not just a minor deduction.

Pick the top {top_n} postings that are the strongest fit for this candidate, ranked \
best-fit first (rank 1 = best). For each pick, give a fit_score from 0-100 and a 2-4 \
sentence rationale explaining specifically why it's a good match (skills overlap, \
seniority match, domain relevance) — be concrete, not generic. Only pick from the \
postings listed above, referencing them by their job_posting_id.
"""


def _format_candidate(candidate: JobCandidate) -> str:
    return (
        f"- job_posting_id={candidate.job_posting_id} | {candidate.title} | "
        f"{candidate.location or 'location not specified'}\n"
        f"  {candidate.description_snippet[:_SNIPPET_LENGTH]}"
    )


def rank_top_matches(
    profile: StructuredProfile, candidates: list[JobCandidate], top_n: int = 3
) -> list[MatchPick]:
    if not candidates:
        return []

    prompt = _PROMPT_TEMPLATE.format(
        seniority=profile.seniority or "not specified",
        experience_years=profile.experience_years,
        skills=", ".join(profile.skills) or "not specified",
        domains=", ".join(profile.domains) or "not specified",
        summary=profile.summary or "not specified",
        candidate_list="\n".join(_format_candidate(c) for c in candidates),
        top_n=top_n,
    )

    output = structured_completion(prompt, _MatchRunOutput, max_tokens=4096)

    valid_ids = {c.job_posting_id for c in candidates}
    picks = [pick for pick in output.picks if pick.job_posting_id in valid_ids]
    return sorted(picks, key=lambda p: p.rank)[:top_n]
