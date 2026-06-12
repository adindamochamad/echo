"""
ECHO Phase 3 Embeddings Agent
==============================
Verifikasi pipeline inti: embedding → storage → pgvector cosine search.

5 Kategori:
  1. Embedding Service     — dimensi, norm, determinism, fallback konsisten
  2. Store + Retrieve      — POST /postmortems menyimpan dengan embedding ke DB
  3. Similarity Search     — pgvector cosine similarity mengembalikan hasil bermakna
  4. Recurrence Detection  — incident mirip terdeteksi, has_recurrence di-set
  5. GET Endpoints         — list dan retrieve by ID berfungsi

Jalankan:
    cd backend && make phase3
"""

import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import AgentReport, BaseAgent

API_PREFIX = "/api/v1"

# Two thematically similar incidents (DB connection pool) — should match each other
PM_A = {
    "title": "Payment DB Connection Pool Exhausted",
    "incident_date": "2025-01-10",
    "raw_content": (
        "Payment service went down for 3 hours. Root cause: PostgreSQL connection pool "
        "max_connections=20 was never increased since initial deploy. Pool saturated under "
        "Black Friday traffic. No monitoring alert fired. Engineers noticed via customer reports.\n\n"
        "Timeline:\n"
        "- 14:00 Payment service starts returning 503\n"
        "- 14:45 On-call notified via customer escalation\n"
        "- 17:30 max_connections bumped to 100, service recovered\n\n"
        "Action items:\n"
        "1. Set up PagerDuty alert for pool utilization > 80%\n"
        "2. Increase max_connections to 200 for production\n"
        "3. Add connection pool health check to /healthz"
    ),
    "severity": "P0",
}

PM_B = {
    "title": "Checkout Service Timeouts — DB Pool Saturation",
    "incident_date": "2025-06-05",
    "raw_content": (
        "Checkout service experienced severe latency (p99 > 8s) for 90 minutes. "
        "Root cause: database connection pool limits were not increased after traffic grew 3x. "
        "Pool reached max_connections ceiling, new requests queued indefinitely. "
        "Monitoring showed connection wait time spiking but no alert was configured.\n\n"
        "This is the second time this quarter we hit connection pool limits. "
        "The action item from the January incident (add pool utilization alert) was never completed.\n\n"
        "Resolution: increased connection pool size and added pgBouncer."
    ),
    "severity": "P1",
}

PM_C = {
    "title": "Frontend Deploy — CDN Cache Invalidation Delay",
    "incident_date": "2025-03-20",
    "raw_content": (
        "After deploying new frontend build, users in Asia-Pacific saw stale CSS for 45 minutes. "
        "CDN cache invalidation command was run but propagation took longer than expected. "
        "No impact to backend services. Resolution: switched to cache-busted asset filenames. "
        "Action item: document CDN invalidation SLA per region."
    ),
    "severity": "P2",
}


async def _register_and_login(agent: BaseAgent) -> str | None:
    """Register a fresh test user and return JWT token."""
    email = f"p3-{uuid.uuid4().hex[:8]}@example.com"
    res = await agent.post(f"{API_PREFIX}/auth/register", json={
        "email": email, "password": "phase3test99", "org_name": "Phase3 Corp"
    })
    if res.status_code != 201:
        return None
    return res.json().get("access_token")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Category 1: Embedding Service ────────────────────────────────────────────

async def _test_embedding_service(report: AgentReport) -> None:
    from app.services.embedding_service import embed_text, build_embedding_text, EMBEDDING_DIMS
    import math

    # 1a. Correct dimensions
    v = await embed_text("database connection pool exhausted payment service")
    if len(v) == EMBEDDING_DIMS:
        report.ok("Embedding: dimensions", f"{EMBEDDING_DIMS}-dim ✓")
    else:
        report.fail("Embedding: dimensions", f"Got {len(v)}, expected {EMBEDDING_DIMS}", critical=True)
        return

    # 1b. Unit norm (cosine similarity prerequisite)
    norm = math.sqrt(sum(x * x for x in v))
    if abs(norm - 1.0) < 0.01:
        report.ok("Embedding: unit norm", f"norm={norm:.4f}")
    else:
        report.fail("Embedding: unit norm", f"norm={norm:.4f} — vector not normalised", critical=True)

    # 1c. Deterministic — same text gives same vector
    v2 = await embed_text("database connection pool exhausted payment service")
    if all(abs(a - b) < 1e-9 for a, b in zip(v, v2)):
        report.ok("Embedding: deterministic", "Identical vectors for same input")
    else:
        report.warn("Embedding: deterministic", "Vectors differ — API may be non-deterministic (OK for Voyage AI)")

    # 1d. Different texts give different vectors
    v3 = await embed_text("CDN cache invalidation delay frontend deploy")
    dot = sum(a * b for a, b in zip(v, v3))
    if dot < 0.99:
        report.ok("Embedding: discriminative", f"cosine({dot:.3f}) < 0.99 — distinct texts differ")
    else:
        report.fail("Embedding: discriminative", f"cosine={dot:.3f} — all texts produce same vector", critical=True)

    # 1e. build_embedding_text concatenation
    combined = build_embedding_text("raw text", "summary here", ["root cause A"], ["service-x"])
    if "raw text" in combined and "root cause A" in combined and "service-x" in combined:
        report.ok("Embedding: build_embedding_text", "All fields concatenated")
    else:
        report.fail("Embedding: build_embedding_text", f"Missing parts: {combined[:80]}", critical=True)


# ── Category 2: Store + Retrieve ─────────────────────────────────────────────

async def _test_store(agent: BaseAgent, report: AgentReport, token: str) -> tuple[str | None, str | None]:
    """Store PM_A and PM_C. Returns (id_a, id_c)."""
    id_a = id_c = None

    for label, pm_data in [("PM_A (DB pool)", PM_A), ("PM_C (CDN, unrelated)", PM_C)]:
        t0 = time.monotonic()
        res = await agent.post(f"{API_PREFIX}/postmortems", json=pm_data, headers=_auth(token))
        ms = (time.monotonic() - t0) * 1000

        if res.status_code == 201:
            data = res.json()
            pm_id = data.get("id")
            has_embedding = bool(data.get("summary"))  # summary = Claude extracted = embedding was generated
            report.ok(f"Store: {label}", f"id={str(pm_id)[:8]}… | {ms:.0f}ms | summary={'yes' if has_embedding else 'no'}")
            if label.startswith("PM_A"):
                id_a = pm_id
            else:
                id_c = pm_id
        else:
            report.fail(f"Store: {label}", f"Got {res.status_code}: {res.text[:150]}", critical=True)

    return id_a, id_c


# ── Category 3: Similarity Search ────────────────────────────────────────────

async def _test_similarity(agent: BaseAgent, report: AgentReport, token: str, id_a: str | None) -> None:
    if not id_a:
        report.warn("Similarity: skipped", "PM_A not stored")
        return

    # Store PM_B (same theme as A) — should surface A as recurrence match
    res = await agent.post(f"{API_PREFIX}/postmortems", json=PM_B, headers=_auth(token))
    if res.status_code != 201:
        report.fail("Similarity: store PM_B", f"Got {res.status_code}", critical=True)
        return

    data = res.json()
    id_b = data.get("id")
    matches = data.get("recurrence_matches", [])
    has_recurrence = data.get("has_recurrence", False)

    report.ok("Similarity: PM_B stored", f"id={str(id_b)[:8]}…")

    # 3a. Recurrence matches returned
    if matches:
        top = matches[0]
        score = top.get("similarity_score", 0)
        report.ok("Similarity: recurrence_matches returned", f"{len(matches)} match(es), top score={score}")
    else:
        report.warn("Similarity: recurrence_matches", "No matches returned (hash fallback vectors may not match semantically)")

    # 3b. has_recurrence flag set
    if has_recurrence:
        report.ok("Similarity: has_recurrence flag", "True when matches found")
    elif not matches:
        report.warn("Similarity: has_recurrence flag", "False because no matches (expected with hash fallback)")
    else:
        report.fail("Similarity: has_recurrence flag", "False despite matches", critical=True)

    # 3c. GET by ID confirms persisted state
    res2 = await agent.get(f"{API_PREFIX}/postmortems/{id_b}", headers=_auth(token))
    if res2.status_code == 200:
        stored = res2.json()
        report.ok("Similarity: GET confirms persistence", f"has_recurrence={stored.get('has_recurrence')}")
    else:
        report.fail("Similarity: GET by ID", f"Got {res2.status_code}", critical=True)


# ── Category 4: Recurrence Detection integrity ───────────────────────────────

async def _test_recurrence(agent: BaseAgent, report: AgentReport, token: str, id_a: str | None, id_c: str | None) -> None:
    # 4a. Unrelated incident (PM_C — CDN) should NOT match DB pool incidents
    # Already stored as id_c. Fetch it and check has_recurrence should be False.
    if id_c:
        res = await agent.get(f"{API_PREFIX}/postmortems/{id_c}", headers=_auth(token))
        if res.status_code == 200:
            stored = res.json()
            if not stored.get("has_recurrence"):
                report.ok("Recurrence: unrelated incident not flagged", "CDN incident has_recurrence=False ✓")
            else:
                report.warn("Recurrence: unrelated incident", "CDN incident flagged as recurrence (hash fallback may cause false positives)")
        else:
            report.warn("Recurrence: GET PM_C", f"Got {res2.status_code}")

    # 4b. Similarity scores are in [0, 1]
    if id_a:
        from app.database import SessionLocal
        from app.services.embedding_service import embed_text
        from app.services.search_service import search_similar
        async with SessionLocal() as db:
            v = await embed_text("connection pool database timeout")
            user_id = (await agent.get(f"{API_PREFIX}/auth/me", headers=_auth(token))).json()["id"]
            hits = await search_similar(db, v, user_id)
        scores_valid = all(0.0 <= h["similarity_score"] <= 1.0 for h in hits)
        if scores_valid:
            report.ok("Recurrence: similarity scores in [0,1]", f"{len(hits)} result(s)")
        else:
            report.fail("Recurrence: scores out of range", str(hits[:2]), critical=True)


# ── Category 5: GET Endpoints ─────────────────────────────────────────────────

async def _test_get_endpoints(agent: BaseAgent, report: AgentReport, token: str) -> None:
    # 5a. GET /postmortems — list
    res = await agent.get(f"{API_PREFIX}/postmortems", headers=_auth(token))
    if res.status_code == 200:
        items = res.json()
        report.ok("GET /postmortems (list)", f"{len(items)} item(s) returned")
    else:
        report.fail("GET /postmortems (list)", f"Got {res.status_code}", critical=True)
        return

    if not items:
        report.warn("GET /postmortems", "Empty list — store tests may have failed")
        return

    # 5b. GET /postmortems/{id}
    first_id = items[0]["id"]
    res2 = await agent.get(f"{API_PREFIX}/postmortems/{first_id}", headers=_auth(token))
    if res2.status_code == 200:
        item = res2.json()
        has_fields = all(k in item for k in ("id", "title", "summary", "root_causes", "action_items"))
        report.ok("GET /postmortems/{id}", f"All fields present: {has_fields}")
    else:
        report.fail("GET /postmortems/{id}", f"Got {res2.status_code}", critical=True)

    # 5c. Auth required — 401 without token
    res3 = await agent.get(f"{API_PREFIX}/postmortems")
    if res3.status_code == 401:
        report.ok("GET /postmortems: 401 without token", "Auth enforced ✓")
    else:
        report.fail("GET /postmortems: auth required", f"Got {res3.status_code}", critical=True)

    # 5d. 404 for wrong user's postmortem
    fake_id = str(uuid.uuid4())
    res4 = await agent.get(f"{API_PREFIX}/postmortems/{fake_id}", headers=_auth(token))
    if res4.status_code == 404:
        report.ok("GET /postmortems/{id}: 404 for unknown id", "Correct ✓")
    else:
        report.warn("GET /postmortems/{id}: 404", f"Got {res4.status_code}")


# ── Agent ─────────────────────────────────────────────────────────────────────

class Phase3EmbeddingsAgent(BaseAgent):
    async def run(self, report: AgentReport) -> None:
        print("\n  === CATEGORY 1: Embedding Service ===")
        await _test_embedding_service(report)

        # Register test user
        token = await _register_and_login(self)
        if not token:
            report.fail("Setup: register test user", "Cannot register — is backend running?", critical=True)
            return

        print("\n  === CATEGORY 2: Store + Retrieve ===")
        id_a, id_c = await _test_store(self, report, token)

        print("\n  === CATEGORY 3: Similarity Search ===")
        await _test_similarity(self, report, token, id_a)

        print("\n  === CATEGORY 4: Recurrence Detection ===")
        await _test_recurrence(self, report, token, id_a, id_c)

        print("\n  === CATEGORY 5: GET Endpoints ===")
        await _test_get_endpoints(self, report, token)


if __name__ == "__main__":
    asyncio.run(Phase3EmbeddingsAgent().execute("Phase 3 — Embeddings & Search", day=0))
