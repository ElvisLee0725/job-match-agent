from app.llm.client import structured_completion
from app.models.job import JobStructuredData

_PROMPT_TEMPLATE = """\
Extract structured data from this job posting description.

Job description:
---
{raw_description}
---

Extract: key requirements (concrete skills/qualifications, as a list), key \
responsibilities (as a list), a one-word-or-short-phrase seniority level (e.g. "junior", \
"mid", "senior", "staff", "manager"), and the primary professional domain/industry this \
role sits in.
"""


def structure_job_posting(raw_description: str) -> JobStructuredData:
    prompt = _PROMPT_TEMPLATE.format(raw_description=raw_description.strip() or "(none)")
    return structured_completion(prompt, JobStructuredData)
