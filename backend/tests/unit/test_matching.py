from types import SimpleNamespace

import pytest

import app.llm.client as llm_client
from app.models.profile import StructuredProfile
from app.services.matching import JobCandidate, rank_top_matches
from tests.unit._support import mock_claude_no_tool_call, mock_claude_tool_response


def _profile() -> StructuredProfile:
    return StructuredProfile(
        skills=["Python", "FastAPI"],
        experience_years=5.0,
        seniority="senior",
        domains=["fintech"],
        summary="Backend engineer.",
    )


def _candidates() -> list[JobCandidate]:
    return [
        JobCandidate(job_posting_id=1, title="Backend Engineer", location="Austin", description_snippet="Build APIs."),
        JobCandidate(job_posting_id=2, title="Data Scientist", location="Remote", description_snippet="Model things."),
    ]


def test_rank_top_matches_returns_picks_sorted_by_rank(monkeypatch):
    mock_claude_tool_response(
        monkeypatch,
        {
            "picks": [
                {"job_posting_id": 2, "rank": 2, "fit_score": 60, "rationale": "decent fit"},
                {"job_posting_id": 1, "rank": 1, "fit_score": 90, "rationale": "great fit"},
            ]
        },
    )

    picks = rank_top_matches(_profile(), _candidates(), top_n=3)

    assert [p.job_posting_id for p in picks] == [1, 2]
    assert picks[0].rank == 1


def test_rank_top_matches_filters_out_ids_not_in_candidate_set(monkeypatch):
    mock_claude_tool_response(
        monkeypatch,
        {
            "picks": [
                {"job_posting_id": 999, "rank": 1, "fit_score": 95, "rationale": "hallucinated id"},
                {"job_posting_id": 1, "rank": 2, "fit_score": 80, "rationale": "real candidate"},
            ]
        },
    )

    picks = rank_top_matches(_profile(), _candidates())

    assert [p.job_posting_id for p in picks] == [1]


def test_rank_top_matches_short_circuits_on_empty_candidates(monkeypatch):
    mock_claude_no_tool_call(monkeypatch)  # would raise if called — proves we never call it

    assert rank_top_matches(_profile(), []) == []


def test_rank_top_matches_raises_on_malformed_response(monkeypatch):
    mock_claude_no_tool_call(monkeypatch)

    with pytest.raises(ValueError):
        rank_top_matches(_profile(), _candidates())


def test_rank_top_matches_prompt_includes_seniority_ceiling_guidance(monkeypatch):
    captured_prompts = []

    class _CapturingClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                captured_prompts.append(kwargs["messages"][0]["content"])
                return SimpleNamespace(
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            name="emit_result",
                            input={"picks": []},
                        )
                    ]
                )

    monkeypatch.setattr(llm_client, "get_client", lambda: _CapturingClient())

    rank_top_matches(_profile(), _candidates())

    assert len(captured_prompts) == 1
    assert "senior" in captured_prompts[0].lower()
    assert "one level above" in captured_prompts[0].lower()
    assert "disqualifying" in captured_prompts[0].lower()
