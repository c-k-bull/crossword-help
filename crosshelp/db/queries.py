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
):
    """Insert a search record into the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO searches (
                    mode, pattern, clue, letters, meaning,
                    result_count, top_result
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (mode, pattern, clue, letters, meaning, result_count, top_result),
            )


def recent_searches(limit: int = 20, mode: Optional[str] = None) -> list[dict]:
    """Return the most recent searches, optionally filtered by mode."""
    base_query = """
        SELECT id, mode, pattern, clue, letters, meaning,
               result_count, top_result, created_at
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