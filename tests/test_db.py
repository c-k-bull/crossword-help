import os
import pytest
from crosshelp.db import queries

@pytest.fixture(autouse=True)
def use_test_database(monkeypatch):
    """Force all DB calls in this module to use the test database"""
    test_url = "postgresql://localhost/crosshelp-test"
    monkeypatch.setattr(queries, "DATABASE_URL", test_url)
    yield
    # Clean up after each test
    with queries.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM searches")

def test_log_search_inserts_row():
    queries.log_search(mode="pattern", pattern="C?T", result_count=3, top_result="CAT")
    rows = queries.recent_searches(limit=10)
    assert len(rows) == 1
    assert rows[0]["mode"] == "pattern"
    assert rows[0]["pattern"] == "C?T"
    assert rows[0]["top_result"] == "CAT"
    assert rows[0]["result_count"] == 3


def test_log_search_with_no_results():
    queries.log_search(mode="pattern", pattern="ZZZZZ", result_count=0)
    rows = queries.recent_searches()
    assert rows[0]["result_count"] == 0
    assert rows[0]["top_result"] is None


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
    assert pattern_rows[0]["pattern"] == "ABC"


def test_recent_searches_respects_limit():
    for i in range(5):
        queries.log_search(mode="pattern", pattern=f"P{i}")
    rows = queries.recent_searches(limit=3)
    assert len(rows) == 3