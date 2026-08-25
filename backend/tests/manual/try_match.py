"""Manual end-to-end sanity check against the REAL app: real DB (backend/data/job_match.db),
real Oracle API, real Claude calls for structuring + ranking. Uses FastAPI's TestClient
in-process (reuses all real router/service logic, no separate server process needed).

Run from backend/: python tests/manual/try_match.py
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_resume.pdf"

client = TestClient(app)


def main() -> None:
    profile_resp = client.get("/api/profile")
    if profile_resp.status_code == 404:
        print("No profile stored yet — uploading the sample resume...")
        files = {"resume_file": ("sample_resume.pdf", FIXTURE.read_bytes(), "application/pdf")}
        data = {
            "background_text": "Looking for senior backend roles at large tech companies.",
            "behavioral_answers": [
                "Tell me about a conflict with a teammate: I disagreed with a peer over an "
                "API design; I proposed we prototype both approaches and benchmark them."
            ],
        }
        profile_resp = client.post("/api/profile/upload", files=files, data=data)
        profile_resp.raise_for_status()
    profile = profile_resp.json()
    print("Profile skills:", profile["structured_profile"]["skills"])
    print("Profile seniority:", profile["structured_profile"]["seniority"])

    print("\nSearching Oracle...")
    scrape_resp = client.post("/api/jobs/scrape", json={"company_name": "oracle", "limit": 50})
    scrape_resp.raise_for_status()
    print(f"Cached {len(scrape_resp.json())} candidate postings.")

    print("\nRanking top matches...")
    match_resp = client.post("/api/match/run", json={"company_name": "oracle"})
    match_resp.raise_for_status()

    for pick in match_resp.json()["results"]:
        print(f"\n#{pick['rank']} ({pick['fit_score']}/100) {pick['title']} — {pick['location']}")
        print(f"  {pick['rationale']}")
        print(f"  {pick['source_url']}")


if __name__ == "__main__":
    main()
