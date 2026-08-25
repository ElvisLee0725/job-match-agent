_US_STATE_ABBREVIATIONS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
    "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV",
    "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


def is_us_location(location: str | None) -> bool:
    if not location:
        return False
    return "united states" in location.lower()


def extract_state_abbreviation(location: str | None) -> str | None:
    if not location:
        return None
    for part in location.split(","):
        token = part.strip().upper()
        if token in _US_STATE_ABBREVIATIONS:
            return token
    return None


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
