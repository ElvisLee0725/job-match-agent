"""Manual sanity check: run the real resume parser + real Claude structuring call.

Requires ANTHROPIC_API_KEY to be set (in backend/.env or the environment).
Run from backend/: python tests/manual/try_resume_parse.py
"""

import json
from pathlib import Path

from app.services.profile_builder import build_structured_profile
from app.services.resume_parser import extract_resume_text

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_resume.pdf"


def main() -> None:
    file_bytes = FIXTURE.read_bytes()
    text = extract_resume_text(FIXTURE.name, file_bytes)
    print("--- extracted resume text ---")
    print(text)

    structured = build_structured_profile(
        resume_text=text,
        background_text="Looking for senior backend roles at large tech companies.",
        behavioral_answers=[
            "Tell me about a conflict with a teammate: I disagreed with a peer over an API "
            "design; I proposed we prototype both approaches and benchmark them, which "
            "resolved the disagreement with data instead of opinion."
        ],
    )
    print("\n--- structured profile ---")
    print(json.dumps(structured.model_dump(), indent=2))


if __name__ == "__main__":
    main()
