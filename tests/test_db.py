import pytest
from crosshelp.db import queries


@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    """Force all DB calls in this module to use the test database."""
    test_url = "postgresql://localhost/crosshelp_test"
    monkeypatch.setattr(queries, "DATABASE_URL", test_url)
    yield
    with queries.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM searches")


def test_log_search_returns_id():
    sid = queries.log_search(mode="pattern", pattern="C?T", result_count=3, top_result="CAT")
    assert isinstance(sid, int)
    assert sid > 0


def test_log_search_inserts_row():
    queries.log_search(mode="pattern", pattern="C?T", result_count=3, top_result="CAT")
    rows = queries.recent_searches(limit=10)
    assert len(rows) == 1
    assert rows[0]["mode"] == "pattern"
    assert rows[0]["pattern"] == "C?T"
    assert rows[0]["top_result"] == "CAT"
    assert rows[0]["was_correct"] is True
    assert rows[0]["corrected_answer"] is None


def test_record_correction_flips_was_correct():
    sid = queries.log_search(mode="clue", clue="With it", pattern="???", top_result="AND")
    ok = queries.record_correction(sid, "HIP")
    assert ok is True
    rows = queries.recent_searches()
    assert rows[0]["was_correct"] is False
    assert rows[0]["corrected_answer"] == "HIP"


def test_record_correction_uppercases_answer():
    sid = queries.log_search(mode="clue", clue="test", pattern="???")
    queries.record_correction(sid, "  hip  ")
    rows = queries.recent_searches()
    assert rows[0]["corrected_answer"] == "HIP"


def test_record_correction_missing_id_returns_false():
    ok = queries.record_correction(999999, "ANYTHING")
    assert ok is False


def test_recent_searches_orders_by_recency():
    queries.log_search(mode="pattern", pattern="FIRST")
    queries.log_search(mode="pattern", pattern="SECOND")
    queries.log_search(mode="pattern", pattern="THIRD")
    rows = queries.recent_searches(limit=10)
    assert [r["pattern"] for r in rows] == ["THIRD", "SECOND", "FIRST"]


def test_recent_searches_filters_by_mode():
    queries.log_search(mode="pattern", pattern="ABC")
    queries.log_search(mode="clue", clue="hello", pattern="?????")
    pattern_rows = queries.recent_searches(mode="pattern")
    assert len(pattern_rows) == 1


def test_accuracy_stats_counts_corrections():
    sid1 = queries.log_search(mode="pattern", pattern="AAA")
    sid2 = queries.log_search(mode="pattern", pattern="BBB")
    queries.log_search(mode="pattern", pattern="CCC")
    queries.record_correction(sid1, "FIX")
    queries.record_correction(sid2, "FIX")

    stats = queries.accuracy_stats()
    assert stats["total"] == 3
    assert stats["reported_wrong"] == 2
    assert stats["reported_wrong_rate"] == pytest.approx(2 / 3)