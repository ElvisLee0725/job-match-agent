from app.models.profile import StructuredProfile
from app.routers import profile as profile_router


def _fake_structured_profile(resume_text, background_text, behavioral_answers):
    return StructuredProfile(
        skills=["Python", "SQL"],
        experience_years=5.0,
        seniority="senior",
        domains=["fintech"],
        summary="Solid backend engineer.",
    )


def test_get_profile_404_when_none_exists(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 404


def test_upload_then_get_profile(client, monkeypatch):
    monkeypatch.setattr(profile_router, "build_structured_profile", _fake_structured_profile)

    files = {"resume_file": ("resume.txt", b"Jordan Smith, backend engineer", "text/plain")}
    data = {
        "background_text": "Loves distributed systems",
        "behavioral_answers": ["Once resolved a conflict by listening first."],
    }
    upload_resp = client.post("/api/profile/upload", files=files, data=data)
    assert upload_resp.status_code == 200
    body = upload_resp.json()
    assert body["structured_profile"]["skills"] == ["Python", "SQL"]
    assert body["background_text"] == "Loves distributed systems"

    get_resp = client.get("/api/profile")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


def test_uploading_twice_overwrites_single_profile_row(client, monkeypatch):
    monkeypatch.setattr(profile_router, "build_structured_profile", _fake_structured_profile)

    first = client.post(
        "/api/profile/upload",
        files={"resume_file": ("resume.txt", b"first version", "text/plain")},
        data={},
    )
    second = client.post(
        "/api/profile/upload",
        files={"resume_file": ("resume.txt", b"second version", "text/plain")},
        data={},
    )

    assert first.json()["id"] == second.json()["id"]
    assert second.json()["raw_resume_text"] == "second version"


def test_update_profile_background_text(client, monkeypatch):
    monkeypatch.setattr(profile_router, "build_structured_profile", _fake_structured_profile)
    client.post(
        "/api/profile/upload",
        files={"resume_file": ("resume.txt", b"resume body", "text/plain")},
        data={},
    )

    resp = client.put("/api/profile", json={"background_text": "Updated background"})
    assert resp.status_code == 200
    assert resp.json()["background_text"] == "Updated background"


def test_update_profile_404_when_none_exists(client):
    resp = client.put("/api/profile", json={"background_text": "no profile yet"})
    assert resp.status_code == 404
