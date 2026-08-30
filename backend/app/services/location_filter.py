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
_REMOTE_TOKEN_PATTERN = re.compile(r"\bremote\b", re.IGNORECASE)


def is_remote_location(location: str | None) -> bool:
    if not location:
        return False
    return bool(_REMOTE_TOKEN_PATTERN.search(location))


def is_us_location(location: str | None) -> bool:
    if not location:
        return False
    if "united states" in location.lower():
        return True
    if _US_TOKEN_PATTERN.search(location):
        return True
    return bool(_STATE_PATTERN.search(location.upper()))


def extract_state_abbreviations(location: str | None) -> list[str]:
    """Returns every state abbreviation mentioned in `location`, not just the first —
    some postings (e.g. Oracle's own multi-location jobs) list more than one, and
    matching only the first would wrongly drop a posting whose primary location isn't
    preferred but whose secondary location is (see `passes_location_filter`)."""
    if not location:
        return []
    return _STATE_PATTERN.findall(location.upper())


def passes_location_filter(
    location: str | None, *, us_only: bool, preferred_states: list[str]
) -> bool:
    """Hard location filter applied before ranking, not left to LLM judgment.

    - Remote postings are always included by default, bypassing both us_only and
      preferred_states — a location naming "remote" (in any format: "Remote", "US
      Remote", "Remote - US") is kept regardless of other settings, since remote roles
      are typically open regardless of specific physical location.
    - us_only excludes anything not identifiable as a US location.
    - preferred_states excludes a posting only when it names specific states, NONE of
      which are in the preferred list — a posting with an unqualified "United States"
      location (often remote-eligible) is kept rather than excluded, since we can't tell
      it actually requires relocation, and a multi-location posting passes if ANY of its
      listed states is preferred, not just the first one mentioned.
    """
    if is_remote_location(location):
        return True

    if us_only and not is_us_location(location):
        return False

    if preferred_states:
        states = extract_state_abbreviations(location)
        preferred_upper = {s.upper() for s in preferred_states}
        if states and not any(s in preferred_upper for s in states):
            return False

    return True
