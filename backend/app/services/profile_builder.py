from app.llm.client import structured_completion
from app.models.profile import StructuredProfile

_PROMPT_TEMPLATE = """\
You are helping structure a job candidate's background so it can later be compared against \
open job postings.

Resume text:
---
{resume_text}
---

Additional background notes from the candidate:
---
{background_text}
---

Sample behavioral interview answers from the candidate (these reveal working style, \
strengths, and the kinds of situations they've handled):
---
{behavioral_answers}
---

Extract a structured profile: a concise list of concrete skills (technical and \
professional), total years of relevant professional experience, a one-word-or-short-phrase \
seniority level (e.g. "junior", "mid", "senior", "staff", "manager"), the professional \
domains/industries they have experience in, and a 2-3 sentence narrative summary capturing \
their strengths and working style (informed by the behavioral answers, not just the resume).
"""


def build_structured_profile(
    resume_text: str, background_text: str, behavioral_answers: list[str]
) -> StructuredProfile:
    prompt = _PROMPT_TEMPLATE.format(
        resume_text=resume_text.strip() or "(none provided)",
        background_text=background_text.strip() or "(none provided)",
        behavioral_answers="\n\n".join(behavioral_answers) or "(none provided)",
    )
    return structured_completion(prompt, StructuredProfile)
