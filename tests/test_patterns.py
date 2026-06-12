from crosshelp.patterns import pattern_to_regex, find_matches, load_words

def test_pattern_to_regex_basic():
    """A simple pattern should match itself."""
    regex = pattern_to_regex("CAT")
    assert regex.match("CAT")
    assert not regex.match("DOG")


def test_pattern_to_regex_wildcards():
    """? should match any letter."""
    regex = pattern_to_regex("C?T")
    assert regex.match("CAT")
    assert regex.match("CUT")
    assert regex.match("COT")
    assert not regex.match("DOG")
    assert not regex.match("CATS")  # wrong length


def test_pattern_to_regex_alternative_wildcards():
    """. and _ should also act as wildcards."""
    regex_dot = pattern_to_regex("C.T")
    regex_under = pattern_to_regex("C_T")
    assert regex_dot.match("CAT")
    assert regex_under.match("CAT")


def test_pattern_to_regex_case_insensitive():
    """Lowercase input should be normalized to uppercase."""
    regex = pattern_to_regex("c?t")
    assert regex.match("CAT")


def test_pattern_to_regex_rejects_invalid_chars():
    """Non-letter, non-wildcard characters should raise ValueError."""
    import pytest
    with pytest.raises(ValueError):
        pattern_to_regex("C@T")
    with pytest.raises(ValueError):
        pattern_to_regex("C5T")

def test_find_matches_returns_known_word():
    """Searching for a known word should return it."""
    results = find_matches("CAT")
    words = [word for word, score in results]
    assert "CAT" in words


def test_find_matches_returns_tuples():
    """Results should be (word, score) tuples."""
    results = find_matches("CAT")
    for item in results:
        assert isinstance(item, tuple)
        assert len(item) == 2
        word, score = item
        assert isinstance(word, str)
        assert isinstance(score, int)


def test_find_matches_respects_limit():
    """Limit parameter should cap result count."""
    results = find_matches("???", limit=5)
    assert len(results) <= 5


def test_find_matches_respects_min_score():
    """min_score should filter low-quality results."""
    results = find_matches("???", min_score=80)
    for word, score in results:
        assert score >= 80


def test_find_matches_sorted_by_score():
    """Results should be sorted by score, highest first."""
    results = find_matches("???", limit=20)
    scores = [score for word, score in results]
    assert scores == sorted(scores, reverse=True)


def test_find_matches_empty_for_impossible_pattern():
    """A pattern no word can match should return empty list."""
    results = find_matches("ZZZZZZZZZZZZZZZ")  # 15 Z's
    assert results == []