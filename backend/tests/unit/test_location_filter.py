from app.services.location_filter import (
    extract_state_abbreviations,
    is_remote_location,
    is_us_location,
    passes_location_filter,
)


def test_is_us_location():
    assert is_us_location("Austin, TX, United States") is True
    assert is_us_location("United States") is True
    assert is_us_location("BENGALURU, KARNATAKA, India") is False
    assert is_us_location(None) is False


def test_is_us_location_handles_non_oracle_formats():
    # Greenhouse/Lever don't spell out "United States" the way Oracle does
    assert is_us_location("US") is True
    assert is_us_location("US / Canada") is True
    assert is_us_location("Seattle, WA") is True
    assert is_us_location("South San Francisco, CA ") is True
    assert is_us_location("London, United Kingdom") is False


def test_extract_state_abbreviations():
    assert extract_state_abbreviations("Nashville, TN, United States") == ["TN"]
    assert extract_state_abbreviations("United States") == []
    assert extract_state_abbreviations("BENGALURU, KARNATAKA, India") == []
    assert extract_state_abbreviations("Seattle, WA") == ["WA"]
    assert extract_state_abbreviations("India") == []  # "IN" must not match inside "INDIA"


def test_extract_state_abbreviations_returns_all_states_in_multi_location_postings():
    # Confirmed with real Oracle data: a posting can list a primary location plus one or
    # more secondary locations, joined by the source into one string (see oracle.py's
    # _combine_locations) — every state mentioned must be extracted, not just the first.
    assert extract_state_abbreviations(
        "Seattle, WA, United States; Santa Clara, CA, United States"
    ) == ["WA", "CA"]


def test_passes_location_filter_excludes_non_us_when_us_only():
    assert passes_location_filter(
        "BENGALURU, KARNATAKA, India", us_only=True, preferred_states=[]
    ) is False
    assert passes_location_filter("Austin, TX, United States", us_only=True, preferred_states=[]) is True


def test_passes_location_filter_excludes_unwanted_specific_state():
    assert passes_location_filter(
        "Nashville, TN, United States", us_only=True, preferred_states=["CA", "TX"]
    ) is False
    assert passes_location_filter(
        "Austin, TX, United States", us_only=True, preferred_states=["CA", "TX"]
    ) is True


def test_passes_location_filter_keeps_unspecified_us_location_even_with_preferred_states():
    # "United States" with no specific state named isn't assumed to require relocation
    assert passes_location_filter(
        "United States", us_only=True, preferred_states=["CA", "TX"]
    ) is True


def test_passes_location_filter_allows_everything_when_no_constraints():
    assert passes_location_filter(
        "BENGALURU, KARNATAKA, India", us_only=False, preferred_states=[]
    ) is True


def test_passes_location_filter_keeps_multi_location_posting_if_any_state_is_preferred():
    # The exact reported scenario: a posting listing Seattle, WA (not preferred) and Santa
    # Clara, CA (preferred) must NOT be excluded just because WA happens to be mentioned
    # first — before the fix, extract_state_abbreviation only checked the first match.
    location = "Seattle, WA, United States; Santa Clara, CA, United States"
    assert passes_location_filter(location, us_only=True, preferred_states=["CA"]) is True


def test_passes_location_filter_excludes_multi_location_posting_if_no_state_is_preferred():
    location = "Seattle, WA, United States; Nashville, TN, United States"
    assert passes_location_filter(location, us_only=True, preferred_states=["CA"]) is False


def test_is_remote_location():
    assert is_remote_location("Remote") is True
    assert is_remote_location("US Remote") is True
    assert is_remote_location("Remote - US") is True
    assert is_remote_location("Austin, TX, United States") is False
    assert is_remote_location(None) is False


def test_passes_location_filter_always_includes_remote_regardless_of_us_only():
    # A bare "Remote" location (real format from Lever's own API) has no country/state
    # info at all, so is_us_location can't identify it as US-based — before this fix that
    # meant it was silently excluded under us_only=True, even though most remote postings
    # from US-headquartered companies are exactly what a US-only searcher wants to see.
    assert passes_location_filter("Remote", us_only=True, preferred_states=[]) is True


def test_passes_location_filter_always_includes_remote_regardless_of_preferred_states():
    assert passes_location_filter("Remote", us_only=True, preferred_states=["CA"]) is True
    assert passes_location_filter("US Remote", us_only=True, preferred_states=["TX"]) is True
