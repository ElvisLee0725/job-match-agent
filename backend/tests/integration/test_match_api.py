from app.models.job import ParsedJobPosting
from app.models.profile import StructuredProfile
from app.routers import jobs as jobs_router
from app.routers import match as match_router
from app.routers import profile as profile_router
from app.services.matching import MatchPick


class _FakeOracleSource:
    def search(self, query, limit=100):
        return [
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/1",
                external_id="1",
                title="Backend Engineer",
                location="Austin, TX, United States",
                raw_description="Build APIs.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/2",
                external_id="2",
                title="Data Scientist",
                location="United States",
                raw_description="Model things.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/3",
                external_id="3",
                title="Backend Engineer (India)",
                location="BENGALURU, KARNATAKA, India",
                raw_description="Build APIs from Bengaluru.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/4",
                external_id="4",
                title="Backend Engineer (Nashville)",
                location="Nashville, TN, United States",
                raw_description="Build APIs from Nashville.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/5",
                external_id="5",
                title="Principal Backend Engineer",
                location="United States",
                raw_description="Lead backend architecture decisions.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/6",
                external_id="6",
                title="Remote Backend Engineer",
                location="Remote",
                raw_description="Fully remote backend role, no country specified.",
            ),
        ]

    def fetch_full_description(self, external_id):
        return "full description"


def _seed_profile(client, monkeypatch) -> None:
    monkeypatch.setattr(
        profile_router,
        "build_structured_profile",
        lambda *a, **k: StructuredProfile(
            skills=["Python"], experience_years=5.0, seniority="senior", domains=["tech"], summary="engineer"
        ),
    )
    client.post(
        "/api/profile/upload",
        files={"resume_file": ("resume.txt", b"resume body", "text/plain")},
        data={},
    )


def _seed_jobs(client, monkeypatch) -> None:
    monkeypatch.setattr(jobs_router, "get_source", lambda company_name: _FakeOracleSource())
    client.post("/api/jobs/scrape", json={"company_name": "oracle", "query": "backend"})


def test_run_match_and_get_latest(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    monkeypatch.setattr(
        match_router,
        "rank_top_matches",
        lambda profile, candidates, top_n=3: [
            MatchPick(job_posting_id=candidates[0].job_posting_id, rank=1, fit_score=88, rationale="Great fit."),
        ],
    )

    resp = client.post("/api/match/run", json={"company_name": "oracle"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["rationale"] == "Great fit."
    assert body["results"][0]["title"] == "Backend Engineer"

    latest = client.get("/api/match/latest", params={"company": "oracle"})
    assert latest.status_code == 200
    assert latest.json()["match_run_id"] == body["match_run_id"]


def test_run_match_without_profile_returns_404(client):
    resp = client.post("/api/match/run", json={"company_name": "oracle"})
    assert resp.status_code == 404


def test_run_match_without_cached_jobs_returns_400(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    resp = client.post("/api/match/run", json={"company_name": "oracle"})
    assert resp.status_code == 400


def test_get_latest_match_404_when_none(client):
    resp = client.get("/api/match/latest", params={"company": "oracle"})
    assert resp.status_code == 404


def test_run_match_excludes_non_us_postings_by_default(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    seen_candidates = []

    def _capture_rank_top_matches(profile, candidates, top_n=3):
        seen_candidates.extend(candidates)
        return []

    monkeypatch.setattr(match_router, "rank_top_matches", _capture_rank_top_matches)

    client.post("/api/match/run", json={"company_name": "oracle"})

    titles = {c.title for c in seen_candidates}
    assert "Backend Engineer (India)" not in titles
    assert "Backend Engineer" in titles  # US postings still included


def test_run_match_excludes_postings_outside_preferred_states(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    client.put("/api/profile", json={"preferred_states": ["TX"]})

    seen_candidates = []

    def _capture_rank_top_matches(profile, candidates, top_n=3):
        seen_candidates.extend(candidates)
        return []

    monkeypatch.setattr(match_router, "rank_top_matches", _capture_rank_top_matches)

    client.post("/api/match/run", json={"company_name": "oracle"})

    titles = {c.title for c in seen_candidates}
    assert "Backend Engineer (Nashville)" not in titles  # TN, not in preferred states
    assert "Backend Engineer" in titles  # Austin, TX — matches preferred state
    assert "Data Scientist" in titles  # unqualified "United States" — kept, not assumed to need relocation
    assert "Remote Backend Engineer" in titles  # remote is always included, regardless of state prefs


def test_run_match_always_includes_remote_postings(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    client.put("/api/profile", json={"us_only": True, "preferred_states": ["CA"]})

    seen_candidates = []

    def _capture_rank_top_matches(profile, candidates, top_n=3):
        seen_candidates.extend(candidates)
        return []

    monkeypatch.setattr(match_router, "rank_top_matches", _capture_rank_top_matches)

    client.post("/api/match/run", json={"company_name": "oracle"})

    titles = {c.title for c in seen_candidates}
    assert "Remote Backend Engineer" in titles


def test_run_match_excludes_postings_matching_excluded_title_keywords(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    client.put("/api/profile", json={"excluded_title_keywords": ["Principal"]})

    seen_candidates = []

    def _capture_rank_top_matches(profile, candidates, top_n=3):
        seen_candidates.extend(candidates)
        return []

    monkeypatch.setattr(match_router, "rank_top_matches", _capture_rank_top_matches)

    client.post("/api/match/run", json={"company_name": "oracle"})

    titles = {c.title for c in seen_candidates}
    assert "Principal Backend Engineer" not in titles
    assert "Backend Engineer" in titles  # unaffected by the exclusion


def test_run_match_includes_principal_title_when_no_exclusion_set(client, monkeypatch):
    _seed_profile(client, monkeypatch)
    _seed_jobs(client, monkeypatch)

    seen_candidates = []

    def _capture_rank_top_matches(profile, candidates, top_n=3):
        seen_candidates.extend(candidates)
        return []

    monkeypatch.setattr(match_router, "rank_top_matches", _capture_rank_top_matches)

    client.post("/api/match/run", json={"company_name": "oracle"})

    titles = {c.title for c in seen_candidates}
    assert "Principal Backend Engineer" in titles


def test_run_match_returns_400_when_all_postings_filtered_out_by_location(client, monkeypatch):
    class _AllInternationalSource:
        def search(self, query, limit=100):
            return [
                ParsedJobPosting(
                    company="oracle",
                    source_type="scraped",
                    source_url="https://careers.oracle.com/en/sites/jobsearch/job/99",
                    external_id="99",
                    title="Backend Engineer (India Only)",
                    location="BENGALURU, KARNATAKA, India",
                    raw_description="Build APIs.",
                )
            ]

        def fetch_full_description(self, external_id):
            return "full description"

    _seed_profile(client, monkeypatch)
    monkeypatch.setattr(jobs_router, "get_source", lambda company_name: _AllInternationalSource())
    client.post("/api/jobs/scrape", json={"company_name": "oracle", "query": "backend"})

    resp = client.post("/api/match/run", json={"company_name": "oracle"})
    assert resp.status_code == 400
    assert "location" in resp.json()["detail"].lower()
