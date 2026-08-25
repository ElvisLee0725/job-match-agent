from app.models.job import ParsedJobPosting
from app.routers import jobs as jobs_router


class _FakeOracleSource:
    company_name = "oracle"

    def search(self, query, limit=100):
        return [
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/1",
                external_id="1",
                title="Senior Backend Engineer",
                location="Austin, TX",
                raw_description="Build things.",
            ),
            ParsedJobPosting(
                company="oracle",
                source_type="scraped",
                source_url="https://careers.oracle.com/en/sites/jobsearch/job/2",
                external_id="2",
                title="Cloud Infrastructure Engineer",
                location="Remote",
                raw_description="Scale infra.",
            ),
        ]

    def fetch_full_description(self, external_id):
        return "full description"


class _FakeUrlParser:
    def parse(self, url, company):
        return ParsedJobPosting(
            company=company,
            source_type="manual_url",
            source_url=url,
            external_id=None,
            title="Platform Engineer",
            location=None,
            raw_description="Great role.",
        )


def test_scrape_jobs_with_explicit_query(client, monkeypatch):
    monkeypatch.setattr(jobs_router, "get_source", lambda company_name: _FakeOracleSource())

    resp = client.post("/api/jobs/scrape", json={"company_name": "oracle", "query": "backend"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["company"] == "oracle"

    list_resp = client.get("/api/jobs", params={"company": "oracle"})
    assert len(list_resp.json()) == 2


def test_scrape_jobs_dedupes_on_second_call(client, monkeypatch):
    monkeypatch.setattr(jobs_router, "get_source", lambda company_name: _FakeOracleSource())
    client.post("/api/jobs/scrape", json={"company_name": "oracle", "query": "backend"})
    resp2 = client.post("/api/jobs/scrape", json={"company_name": "oracle", "query": "backend"})
    assert resp2.status_code == 200

    list_resp = client.get("/api/jobs", params={"company": "oracle"})
    assert len(list_resp.json()) == 2


def test_scrape_jobs_without_query_and_without_profile_returns_400(client, monkeypatch):
    monkeypatch.setattr(jobs_router, "get_source", lambda company_name: _FakeOracleSource())
    resp = client.post("/api/jobs/scrape", json={"company_name": "oracle"})
    assert resp.status_code == 400


def test_scrape_jobs_unsupported_company_returns_400(client):
    resp = client.post("/api/jobs/scrape", json={"company_name": "totallyfakecompany"})
    assert resp.status_code == 400


def test_parse_url_endpoint(client, monkeypatch):
    from app.models.job import JobStructuredData

    monkeypatch.setattr(jobs_router, "SingleUrlJobParser", lambda: _FakeUrlParser())
    monkeypatch.setattr(
        jobs_router,
        "structure_job_posting",
        lambda raw_description: JobStructuredData(
            requirements=["Python"], responsibilities=["Ship features"], seniority="mid", domain="tech"
        ),
    )

    resp = client.post(
        "/api/jobs/parse-url", json={"url": "https://linkedin.com/jobs/1", "company": "acme"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source_type"] == "manual_url"
    assert body["title"] == "Platform Engineer"
    assert body["structured"]["seniority"] == "mid"
