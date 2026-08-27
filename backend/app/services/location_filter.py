import re

_US_STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

# Different job boards format US locations very differently: Oracle spells out
# "United States", Greenhouse/Lever often just say "US" or "US / Canada", or give only a
# bare state abbreviation ("Seattle, WA") with no country at all. Match all of them via
# word-boundary regexes rather than a single literal substring, so this works across
# platforms — not just the one it was originally written against.
_US_TOKEN_PATTERN = re.compile(r"\b(?:US|USA)\b")
_STATE_PATTERN = re.compile(r"\b(" + "|".join(sorted(_US_STATE_ABBREVIATIONS)) + r")\b")


def is_us_location(location: str | None) -> bool:
    if not location:
        return False
    if "united states" in location.lower():
        return True
    if _US_TOKEN_PATTERN.search(location):
        return True
    return bool(_STATE_PATTERN.search(location.upper()))


def extract_state_abbreviation(location: str | None) -> str | None:
    if not location:
        return None
    match = _STATE_PATTERN.search(location.upper())
    return match.group(1) if match else None


def passes_location_filter(
    location: str | None, *, us_only: bool, preferred_states: list[str]
) -> bool:
    """Hard location filter applied before ranking, not left to LLM judgment.

    - us_only excludes anything not identifiable as a US location.
    - preferred_states excludes a posting only when it names a *specific* state that
      isn't in the preferred list — a posting with an unqualified "United States"
      location (often remote-eligible or multi-location) is kept rather than excluded,
      since we can't tell it actually requires relocation.
    """
    if us_only and not is_us_location(location):
        return False

    if preferred_states:
        state = extract_state_abbreviation(location)
        if state is not None and state.upper() not in {s.upper() for s in preferred_states}:
            return False

    return True
