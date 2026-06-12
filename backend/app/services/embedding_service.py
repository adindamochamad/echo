"""
Embedding service — Voyage AI (voyage-3-large, 1024 dims).

If VOYAGE_API_KEY is not configured, falls back to a deterministic hash-based
vector so the rest of the pipeline (pgvector, cosine search) keeps working.
The fallback does NOT produce semantic embeddings — it exists only so the
system is functional end-to-end during local dev without a key.
"""

import hashlib
import logging

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMS = 1024
_voyage_client = None


def _get_voyage():
    global _voyage_client
    if _voyage_client is None and settings.VOYAGE_API_KEY:
        import voyageai
        _voyage_client = voyageai.AsyncClient(api_key=settings.VOYAGE_API_KEY)
    return _voyage_client


def _hash_embed(text: str) -> list[float]:
    """Deterministic pseudo-embedding — same text → same vector. NOT semantic."""
    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2 ** 32)
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(EMBEDDING_DIMS).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


async def embed_text(text: str) -> list[float]:
    """Generate a single 1024-dim embedding for text."""
    client = _get_voyage()
    if client is None:
        logger.debug("VOYAGE_API_KEY not set — using hash fallback embedding")
        return _hash_embed(text)

    try:
        result = await client.embed([text], model="voyage-3-large", input_type="document")
        return result.embeddings[0]
    except Exception as exc:
        logger.warning("Voyage AI embed failed (%s) — falling back to hash", exc)
        return _hash_embed(text)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in one API call."""
    if not texts:
        return []

    client = _get_voyage()
    if client is None:
        return [_hash_embed(t) for t in texts]

    try:
        result = await client.embed(texts, model="voyage-3-large", input_type="document")
        return result.embeddings
    except Exception as exc:
        logger.warning("Voyage AI batch embed failed (%s) — falling back to hash", exc)
        return [_hash_embed(t) for t in texts]


def build_embedding_text(raw_content: str, summary: str, root_causes: list[str], systems_affected: list[str]) -> str:
    """Concatenate fields to form the text that gets embedded — mirrors what search queries against."""
    parts = [raw_content, summary]
    parts.extend(root_causes)
    parts.extend(systems_affected)
    return " ".join(p for p in parts if p)
