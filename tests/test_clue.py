from crosshelp.clue import _parse_candidates, _filter_by_pattern


def test_parse_candidates_basic():
    """Simple line-separated output should parse cleanly."""
    raw = "PARIS\nLYON\nNICE"
    result = _parse_candidates(raw)
    assert result == ["PARIS", "LYON", "NICE"]


def test_parse_candidates_strips_punctuation():
    """Numbered lists and punctuation should be stripped."""
    raw = "1. PARIS\n2. LYON!\n- NICE"
    result = _parse_candidates(raw)
    assert "PARIS" in result
    assert "LYON" in result
    assert "NICE" in result


def test_parse_candidates_handles_blank_lines():
    """Blank lines should be skipped."""
    raw = "PARIS\n\nLYON\n\n\nNICE"
    result = _parse_candidates(raw)
    assert result == ["PARIS", "LYON", "NICE"]


def test_parse_candidates_uppercases():
    """Mixed-case input should be normalized to uppercase."""
    raw = "paris\nLyon\nNICE"
    result = _parse_candidates(raw)
    assert result == ["PARIS", "LYON", "NICE"]


def test_filter_by_pattern_keeps_matches():
    """Only candidates matching the pattern should survive."""
    candidates = ["PARIS", "LYON", "NICE", "TOKYO"]
    result = _filter_by_pattern(candidates, "?????")
    # 5-letter cities only
    assert "PARIS" in result
    assert "TOKYO" in result
    assert "LYON" not in result   # 4 letters
    assert "NICE" not in result   # 4 letters


def test_filter_by_pattern_respects_fixed_letters():
    """Fixed letters in pattern must match candidates."""
    candidates = ["PARIS", "TOKYO", "MILAN"]
    result = _filter_by_pattern(candidates, "P????")
    assert "PARIS" in result
    assert "TOKYO" not in result
    assert "MILAN" not in result