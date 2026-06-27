"""
Database access for crosshelp.

Wraps psycopg operations in a small, testable API.
"""

import os
from contextlib import contextmanager
from typing import Optional

import psycopg


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://localhost/crosshelp",
)


@contextmanager
def get_connection():
    """Context manager that yields a Postgres connection and ensures cleanup."""
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_search(
    mode: str,
    pattern: Optional[str] = None,
    clue: Optional[str] = None,
    letters: Optional[str] = None,
    meaning: Optional[str] = None,
    result_count: int = 0,
    top_result: Optional[str] = None,
) -> int:
    """Insert a search record and return its id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO searches (
                    mode, pattern, clue, letters, meaning,
                    result_count, top_result
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (mode, pattern, clue, letters, meaning, result_count, top_result),
            )
            return cur.fetchone()[0]

def record_correction(search_id: int, corrected_answer: str) -> bool:
    """
    Mark a search as incorrect and record the user-supplied correct answer.

    Returns True if the row was updated, False if no such id exists.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE searches
                SET was_correct = FALSE,
                    corrected_answer = %s
                WHERE id = %s
                """,
                (corrected_answer.upper().strip(), search_id),
            )
            return cur.rowcount > 0

def recent_searches(limit: int = 20, mode: Optional[str] = None) -> list[dict]:
    """Return the most recent searches, optionally filtered by mode."""
    base_query = """
        SELECT id, mode, pattern, clue, letters, meaning,
               result_count, top_result, was_correct, corrected_answer,
               created_at
        FROM searches
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if mode:
                cur.execute(
                    base_query + " WHERE mode = %s ORDER BY created_at DESC LIMIT %s",
                    (mode, limit),
                )
            else:
                cur.execute(
                    base_query + " ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        
def accuracy_stats(mode: Optional[str] = None) -> dict:
    """Return reported accuracy statistics."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if mode:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE was_correct = FALSE) AS reported_wrong
                        FROM searches
                        WHERE mode = %s
                    """,
                    (mode,),
                )
            else:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE was_correct = FALSE) AS reported_wrong
                    FROM searches
                    """
                )
            total, reported_wrong = cur.fetchone()
            return {
                "total": total,
                "reported_wrong": reported_wrong,
                "reported_wrong_rate": (reported_wrong / total) if total else 0.0,
            }