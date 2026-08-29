from app.services.title_filter import passes_title_filter


def test_passes_title_filter_allows_everything_when_no_exclusions():
    assert passes_title_filter("Principal Software Engineer", []) is True


def test_passes_title_filter_excludes_matching_keyword_case_insensitively():
    assert passes_title_filter("Principal Software Engineer", ["principal"]) is False
    assert passes_title_filter("PRINCIPAL Software Engineer", ["Principal"]) is False


def test_passes_title_filter_keeps_non_matching_titles():
    assert passes_title_filter("Senior Software Engineer", ["Principal", "Director"]) is True


def test_passes_title_filter_matches_any_of_multiple_keywords():
    assert passes_title_filter("Director of Engineering", ["Principal", "Director"]) is False


def test_passes_title_filter_ignores_blank_keywords():
    assert passes_title_filter("Senior Software Engineer", ["", "  "]) is True
