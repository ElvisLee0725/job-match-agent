from app.sources.keyword_filter import filter_and_rank_by_keyword, keyword_match_score


def test_keyword_match_score_counts_distinct_matching_words():
    assert keyword_match_score("Senior Backend Engineer", "backend engineer") == 2
    assert keyword_match_score("Senior Backend Engineer", "backend backend") == 1
    assert keyword_match_score("Data Scientist", "backend engineer") == 0


def test_filter_and_rank_by_keyword_excludes_zero_score_and_sorts_by_score():
    items = [
        {"title": "Data Scientist"},
        {"title": "Senior Backend Engineer"},
        {"title": "Backend Engineer II"},
    ]

    result = filter_and_rank_by_keyword(items, "senior backend engineer", get_title=lambda i: i["title"], limit=10)

    titles = [i["title"] for i in result]
    assert titles == ["Senior Backend Engineer", "Backend Engineer II"]


def test_filter_and_rank_by_keyword_respects_limit():
    items = [{"title": f"Backend Engineer {i}"} for i in range(5)]

    result = filter_and_rank_by_keyword(items, "backend", get_title=lambda i: i["title"], limit=2)

    assert len(result) == 2
