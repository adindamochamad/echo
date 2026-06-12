"""
pgvector similarity search — real cosine similarity against stored postmortems.

Replaces the Jaccard/keyword matching in matching_service.py for authenticated
users who have data in the database.
"""

import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.30  # cosine similarity floor (0=orthogonal, 1=identical)
MAX_RESULTS = 5


async def search_similar(
    db: AsyncSession,
    query_embedding: list[float],
    user_id: str,
    exclude_id: str | None = None,
    limit: int = MAX_RESULTS,
) -> list[dict]:
    """
    Find postmortems most similar to query_embedding using pgvector cosine distance.
    Returns dicts with keys: id, title, incident_date, similarity_score, action_items.
    """
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    exclude_clause = "AND id != :exclude_id" if exclude_id else ""

    sql = text(f"""
        SELECT
            id,
            title,
            incident_date,
            action_items,
            1 - (embedding <=> CAST(:vec AS vector)) AS similarity_score
        FROM postmortems
        WHERE user_id = :user_id
          AND embedding IS NOT NULL
          {exclude_clause}
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :limit
    """)

    params: dict = {"vec": vec_str, "user_id": user_id, "limit": limit}
    if exclude_id:
        params["exclude_id"] = exclude_id

    try:
        rows = (await db.execute(sql, params)).fetchall()
    except Exception as exc:
        logger.error("pgvector search failed: %s", exc)
        return []

    results = []
    for row in rows:
        score = float(row.similarity_score)
        if score < SIMILARITY_THRESHOLD:
            continue
        results.append({
            "id": str(row.id),
            "title": row.title,
            "incident_date": row.incident_date,
            "similarity_score": round(score, 4),
            "action_items": row.action_items or [],
        })

    return results


def days_between(date_a: str, date_b: str | None = None) -> int:
    """Days between two ISO date strings. date_b defaults to today."""
    try:
        d_a = date.fromisoformat(date_a)
        d_b = date.fromisoformat(date_b) if date_b else date.today()
        return abs((d_b - d_a).days)
    except ValueError:
        return 0
