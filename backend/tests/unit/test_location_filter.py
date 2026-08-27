from app.services.location_filter import (
    extract_state_abbreviation,
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


def test_extract_state_abbreviation():
    assert extract_state_abbreviation("Nashville, TN, United States") == "TN"
    assert extract_state_abbreviation("United States") is None
    assert extract_state_abbreviation("BENGALURU, KARNATAKA, India") is None
    assert extract_state_abbreviation("Seattle, WA") == "WA"
    assert extract_state_abbreviation("India") is None  # "IN" must not match inside "INDIA"


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
