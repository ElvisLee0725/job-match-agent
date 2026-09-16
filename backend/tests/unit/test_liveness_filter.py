from dataclasses import dataclass

import httpx

from app.services.liveness_filter import filter_still_live


@dataclass
class _FakePosting:
    id: int
    external_id: str | None


class _FakeSource:
    def __init__(self, live_ids: set[str]):
        self._live_ids = live_ids

    def check_exists(self, external_id: str) -> bool:
        return external_id in self._live_ids


class _FlakySource:
    def check_exists(self, external_id: str) -> bool:
        raise httpx.ConnectError("boom")


def test_filter_still_live_drops_postings_the_source_no_longer_has():
    postings = [_FakePosting(1, "a"), _FakePosting(2, "b"), _FakePosting(3, "c")]
    source = _FakeSource(live_ids={"a", "c"})

    result = filter_still_live(postings, source)

    assert [p.id for p in result] == [1, 3]


def test_filter_still_live_keeps_postings_with_no_external_id():
    postings = [_FakePosting(1, None)]
    source = _FakeSource(live_ids=set())

    assert filter_still_live(postings, source) == postings


def test_filter_still_live_returns_postings_unchanged_when_source_is_none():
    postings = [_FakePosting(1, "a")]

    assert filter_still_live(postings, None) == postings


def test_filter_still_live_fails_open_on_network_errors():
    postings = [_FakePosting(1, "a")]

    assert filter_still_live(postings, _FlakySource()) == postings
