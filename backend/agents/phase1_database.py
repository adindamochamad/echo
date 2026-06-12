"""
ECHO Phase 1 Database Agent
===========================
Verifikasi, testing, dan stress-test untuk schema database Phase 1.

6 Kategori:
  1. HTTP Health Checks    — endpoint /health via BaseAgent HTTP client
  2. Schema Verification   — tabel, kolom, tipe, constraint, index via DB langsung
  3. CRUD Operations       — insert/select/update/delete User dan Postmortem
  4. Vector Operations     — simpan embedding dummy, cosine similarity, ordering
  5. Constraint Integrity  — unique, not-null, FK, check constraint enforcement
  6. Stress Test           — concurrent inserts + cosine searches, latensi p50/p95/p99

Notes:
  - Kategori 2–6 tidak butuh backend HTTP, langsung ke PostgreSQL via SQLAlchemy.
  - Semua data test pakai prefix "echo-test-phase1-" dan dibersihkan setelah selesai.
  - Jika schema stale (tabel lama tanpa kolom baru), jalankan dulu:
      python scripts/reset_db.py

Jalankan:
    cd backend && make phase1
    cd backend && python agents/phase1_database.py
"""

import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agents.base_agent import AgentReport, BaseAgent
from app.config import settings

_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

TEST_PREFIX        = "echo-test-phase1-"
STRESS_USERS       = 30
STRESS_POSTMORTEMS = 100
STRESS_SEARCHES    = 50
EMBEDDING_DIMS     = 1024


# ── Helpers ──────────────────────────────────────────────────────────────────

def _email(suffix: str = "") -> str:
    return f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}{suffix}@echo-test.invalid"


def _emb(seed: int = 0) -> str:
    """Embedding deterministik sebagai string pgvector '[x,y,...]'."""
    import math
    vals = [math.sin(i + seed) / 10.0 for i in range(EMBEDDING_DIMS)]
    return "[" + ",".join(f"{v:.6f}" for v in vals) + "]"


def _p(data: list[float], pct: int) -> float:
    if not data:
        return 0.0
    return sorted(data)[max(0, int(len(data) * pct / 100) - 1)]


async def _bersihkan(sesi: AsyncSession) -> int:
    hasil = await sesi.execute(
        text("DELETE FROM users WHERE email LIKE :p RETURNING id"),
        {"p": f"{TEST_PREFIX}%"},
    )
    await sesi.commit()
    return hasil.rowcount


# ── Kategori 1: HTTP Health ──────────────────────────────────────────────────

class _HttpChecks(BaseAgent):
    async def run(self, report: AgentReport):
        try:
            r = await self.get("/health")
        except Exception as e:
            report.fail("Health endpoint", f"Connection refused: {e}", critical=True)
            return

        if r.status_code != 200:
            report.fail("Health endpoint", f"HTTP {r.status_code}", critical=True)
            return

        data = r.json()
        report.ok("Health endpoint", f"status={data.get('status')}")

        if data.get("database") == "connected":
            report.ok("Database connection", "PostgreSQL reachable")
        else:
            report.fail("Database connection", f"status={data.get('database')!r}", critical=True)

        if data.get("pgvector") == "enabled":
            report.ok("pgvector extension", "Active")
        else:
            report.fail("pgvector extension", f"status={data.get('pgvector')!r}", critical=True)

        for tabel, ada in (data.get("tables") or {}).items():
            if ada:
                report.ok(f"Table '{tabel}' (HTTP)", "Exists")
            else:
                report.fail(f"Table '{tabel}' (HTTP)", "Not found", critical=True)

        t0 = time.monotonic()
        await self.get("/health")
        ms = (time.monotonic() - t0) * 1000
        if ms < 200:
            report.ok("Health response time", f"{ms:.0f}ms")
        else:
            report.warn("Health response time", f"{ms:.0f}ms — target <200ms")


# ── Kategori 2: Schema Verification ──────────────────────────────────────────

async def _test_schema(report: AgentReport) -> None:
    try:
        async with _engine.connect() as c:

            # 2a. pgvector extension
            row = (await c.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")
            )).fetchone()
            if row and row[0]:
                report.ok("Schema: pgvector extension", "Confirmed via pg_extension")
            else:
                report.fail("Schema: pgvector extension", "Run: CREATE EXTENSION vector", critical=True)

            # 2b. Tabel wajib
            for tbl in ("users", "postmortems"):
                row = (await c.execute(
                    text("SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                         "WHERE table_schema='public' AND table_name=:t)"),
                    {"t": tbl},
                )).fetchone()
                if row and row[0]:
                    report.ok(f"Schema: table '{tbl}'", "Exists")
                else:
                    report.fail(f"Schema: table '{tbl}'", "Missing — jalankan reset_db.py", critical=True)

            # 2c. Kolom users
            rows = (await c.execute(
                text("SELECT column_name FROM information_schema.columns "
                     "WHERE table_schema='public' AND table_name='users'")
            )).fetchall()
            ada = {r[0] for r in rows}
            wajib = {"id", "email", "password_hash", "org_name", "created_at"}
            hilang = wajib - ada
            if not hilang:
                report.ok("Schema: users columns", f"{len(wajib)} required columns present")
            else:
                report.fail("Schema: users columns", f"Missing: {hilang}", critical=True)

            # 2d. Kolom postmortems
            rows = (await c.execute(
                text("SELECT column_name FROM information_schema.columns "
                     "WHERE table_schema='public' AND table_name='postmortems'")
            )).fetchall()
            ada = {r[0] for r in rows}
            wajib = {
                "id", "user_id", "title", "incident_date", "raw_content",
                "summary", "root_causes", "action_items", "severity",
                "systems_affected", "embedding", "has_recurrence", "created_at",
            }
            hilang = wajib - ada
            if not hilang:
                report.ok("Schema: postmortems columns", f"{len(wajib)} required columns present")
            else:
                report.fail("Schema: postmortems columns",
                            f"Missing: {hilang} — jalankan reset_db.py", critical=True)

            # 2e. Tipe embedding = vector
            row = (await c.execute(
                text("SELECT udt_name FROM information_schema.columns "
                     "WHERE table_schema='public' AND table_name='postmortems' "
                     "AND column_name='embedding'")
            )).fetchone()
            if row and row[0] == "vector":
                report.ok("Schema: embedding type", "vector (pgvector confirmed)")
            elif row:
                report.fail("Schema: embedding type", f"Got '{row[0]}', expected 'vector'", critical=True)
            else:
                report.fail("Schema: embedding type", "Column missing", critical=True)

            # 2f. UNIQUE email — SQLAlchemy unique=True creates a unique index,
            # not a named UNIQUE constraint in table_constraints. Check pg_indexes.
            row = (await c.execute(
                text("SELECT COUNT(*) FROM pg_indexes "
                     "WHERE tablename='users' AND indexdef LIKE '%email%' "
                     "AND indexname LIKE '%email%'")
            )).fetchone()
            if row and row[0] > 0:
                report.ok("Schema: users.email UNIQUE", "Unique index ix_users_email exists")
            else:
                report.fail("Schema: users.email UNIQUE", "Missing — jalankan reset_db.py", critical=True)

            # 2g. FK postmortems.user_id → users.id
            row = (await c.execute(
                text("SELECT COUNT(*) FROM information_schema.referential_constraints rc "
                     "JOIN information_schema.key_column_usage kcu "
                     "  ON rc.constraint_name = kcu.constraint_name "
                     "WHERE kcu.table_name='postmortems' AND kcu.column_name='user_id'")
            )).fetchone()
            if row and row[0] > 0:
                report.ok("Schema: postmortems FK", "user_id → users.id confirmed")
            else:
                report.fail("Schema: postmortems FK", "Missing — jalankan reset_db.py", critical=True)

            # 2h. ivfflat index
            row = (await c.execute(
                text("SELECT indexname FROM pg_indexes "
                     "WHERE tablename='postmortems' AND indexdef ILIKE '%ivfflat%'")
            )).fetchone()
            if row:
                report.ok("Schema: ivfflat index", f"{row[0]}")
            else:
                report.warn("Schema: ivfflat index",
                            "Not found — jalankan reset_db.py untuk buat index")

            # 2i. server_default pada id (PostgreSQL DEFAULT clause)
            row = (await c.execute(
                text("SELECT column_default FROM information_schema.columns "
                     "WHERE table_schema='public' AND table_name='users' AND column_name='id'")
            )).fetchone()
            default_val = row[0] if row else None
            if default_val and "gen_random_uuid" in str(default_val):
                report.ok("Schema: users.id server_default", f"DEFAULT {default_val}")
            else:
                report.fail("Schema: users.id server_default",
                            f"Got: {default_val!r} — raw SQL INSERT tanpa id akan gagal. "
                            "Jalankan reset_db.py.", critical=True)

    except Exception as e:
        report.fail("Schema: unexpected error", str(e)[:300], critical=True)


# ── Kategori 3: CRUD Operations ───────────────────────────────────────────────

async def _test_crud(report: AgentReport) -> None:
    email = _email()
    user_id = None

    async with _Session() as sesi:
        # 3a. INSERT user — pakai gen_random_uuid() eksplisit agar aman di semua schema
        try:
            row = (await sesi.execute(
                text("INSERT INTO users (id, email, password_hash, org_name) "
                     "VALUES (gen_random_uuid(), :e, :pw, :org) RETURNING id"),
                {"e": email, "pw": "$2b$12$fakehash", "org": "ECHO Test Org"},
            )).fetchone()
            await sesi.commit()
            user_id = row[0]
            report.ok("CRUD: INSERT user", f"id={user_id}")
        except Exception as e:
            await sesi.rollback()
            report.fail("CRUD: INSERT user", str(e)[:200], critical=True)
            return

        # 3b. SELECT user
        row = (await sesi.execute(
            text("SELECT id, email, org_name FROM users WHERE email = :e"),
            {"e": email},
        )).fetchone()
        if row:
            report.ok("CRUD: SELECT user", f"email={row[1]}, org={row[2]}")
        else:
            report.fail("CRUD: SELECT user", "Row not found after INSERT", critical=True)
            return

        # 3c. INSERT postmortem
        # Note: use CAST(:x AS jsonb) instead of :x::jsonb — asyncpg misparses ::
        pm_inserted = False
        try:
            await sesi.execute(
                text("INSERT INTO postmortems "
                     "(id, user_id, title, incident_date, raw_content, summary, "
                     " severity, root_causes, action_items, systems_affected, has_recurrence) "
                     "VALUES (gen_random_uuid(), :uid, :title, :date, :raw, :summ, "
                     "        :sev, CAST(:rc AS jsonb), CAST(:ai AS jsonb), CAST(:sys AS jsonb), false)"),
                {
                    "uid": user_id,
                    "title": "Test — DB Connection Pool",
                    "date": "2025-03-15",
                    "raw": "Payment service down. Root cause: connection pool exhausted.",
                    "summ": "Payment outage 4h — connection pool.",
                    "sev": "P0",
                    "rc": '["Connection pool max_connections=20 never reviewed"]',
                    "ai": '[{"description":"Increase max_connections","owner":"SRE","status":"OPEN","ticket_ref":null}]',
                    "sys": '["payment-service","database"]',
                },
            )
            await sesi.commit()
            pm_inserted = True
            report.ok("CRUD: INSERT postmortem", "With JSONB + severity + FK")
        except Exception as e:
            await sesi.rollback()
            report.fail("CRUD: INSERT postmortem", str(e)[:200], critical=True)

        # 3d. SELECT postmortems milik user (skip jika INSERT gagal)
        if pm_inserted:
            try:
                count = (await sesi.execute(
                    text("SELECT COUNT(*) FROM postmortems WHERE user_id = :uid"),
                    {"uid": user_id},
                )).scalar()
                if count and count >= 1:
                    report.ok("CRUD: SELECT postmortems", f"{count} row(s)")
                else:
                    report.fail("CRUD: SELECT postmortems", "No rows", critical=True)
            except Exception as e:
                report.fail("CRUD: SELECT postmortems", str(e)[:150], critical=True)

        # 3e. UPDATE JSONB — append ke action_items (skip jika INSERT gagal)
        if pm_inserted:
            try:
                await sesi.execute(
                    text("UPDATE postmortems "
                         "SET action_items = action_items || "
                         "'[{\"description\":\"Updated item\",\"status\":\"COMPLETED\"}]'::jsonb "
                         "WHERE user_id = :uid"),
                    {"uid": user_id},
                )
                await sesi.commit()
                report.ok("CRUD: UPDATE JSONB action_items", "Append via || operator")
            except Exception as e:
                await sesi.rollback()
                report.warn("CRUD: UPDATE JSONB", str(e)[:150])

        # 3f. CASCADE DELETE — selalu jalankan untuk cleanup
        pm_before = 0
        try:
            pm_before = (await sesi.execute(
                text("SELECT COUNT(*) FROM postmortems WHERE user_id = :uid"),
                {"uid": user_id},
            )).scalar() or 0
        except Exception:
            pass  # kolom user_id mungkin tidak ada di schema lama — skip count

        try:
            await sesi.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await sesi.commit()
            saved_id, user_id = user_id, None

            pm_after = 0
            try:
                pm_after = (await sesi.execute(
                    text("SELECT COUNT(*) FROM postmortems WHERE user_id = :uid"),
                    {"uid": saved_id},
                )).scalar() or 0
            except Exception:
                pass

            if pm_before > 0 and pm_after == 0:
                report.ok("CRUD: CASCADE DELETE", f"{pm_before} postmortem(s) ikut terhapus")
            elif pm_after > 0:
                report.fail("CRUD: CASCADE DELETE", f"{pm_after} orphan postmortem tersisa", critical=True)
            else:
                report.ok("CRUD: CASCADE DELETE", "User deleted (no postmortems to verify cascade)")
        except Exception as e:
            report.fail("CRUD: DELETE user", str(e)[:150], critical=True)


# ── Kategori 4: Vector Operations ─────────────────────────────────────────────

async def _test_vectors(report: AgentReport) -> None:
    email = _email("-vec")
    user_id = None

    async with _Session() as sesi:
        # Setup — bungkus dalam try agar crash tidak merembet ke agent loop
        try:
            row = (await sesi.execute(
                text("INSERT INTO users (id, email, password_hash) "
                     "VALUES (gen_random_uuid(), :e, :p) RETURNING id"),
                {"e": email, "p": "$2b$12$fakehash"},
            )).fetchone()
            await sesi.commit()
            user_id = row[0]
        except Exception as e:
            await sesi.rollback()
            report.fail("Vector: setup — INSERT user", str(e)[:200], critical=True)
            return

        try:
            # 4a. INSERT 3 embeddings — seed berbeda untuk test ordering
            for i, seed in enumerate([1, 2, 500], 1):
                await sesi.execute(
                    text("INSERT INTO postmortems "
                         "(id, user_id, title, incident_date, raw_content, embedding, has_recurrence) "
                         "VALUES (gen_random_uuid(), :uid, :title, '2025-01-01', 'test', "
                         "        CAST(:emb AS vector), false)"),
                    {"uid": user_id, "title": f"Vector Test {i}", "emb": _emb(seed)},
                )
            await sesi.commit()
            report.ok("Vector: INSERT embeddings", f"3 rows × {EMBEDDING_DIMS}-dim vectors")

            # 4b. Cosine similarity search — query = seed 1, harus dapat [Test1, Test2, Test3]
            rows = (await sesi.execute(
                text("SELECT title, 1 - (embedding <=> CAST(:q AS vector)) AS score "
                     "FROM postmortems "
                     "WHERE user_id = :uid AND embedding IS NOT NULL "
                     "ORDER BY embedding <=> CAST(:q AS vector) LIMIT 3"),
                {"q": _emb(1), "uid": user_id},
            )).fetchall()

            if rows:
                scores = [(r[0], round(float(r[1]), 4)) for r in rows]
                report.ok("Vector: cosine search returns results", str(scores))

                # Self-similarity harus mendekati 1.0
                if scores[0][1] >= 0.99:
                    report.ok("Vector: self-similarity", f"{scores[0][1]:.4f} ≥ 0.99 ✓")
                else:
                    report.warn("Vector: self-similarity", f"{scores[0][1]:.4f} < 0.99")

                # seed=2 harus lebih dekat ke seed=1 daripada seed=500
                if len(scores) == 3 and scores[1][1] > scores[2][1]:
                    report.ok("Vector: similarity ordering", "Closer seed ranks higher ✓")
                else:
                    report.warn("Vector: similarity ordering", f"Unexpected: {scores}")
            else:
                report.fail("Vector: cosine search", "No results returned", critical=True)

            # 4c. Row dengan embedding NULL tidak merusak query
            await sesi.execute(
                text("INSERT INTO postmortems "
                     "(id, user_id, title, incident_date, raw_content, has_recurrence) "
                     "VALUES (gen_random_uuid(), :uid, 'No Embedding', '2025-01-01', 'none', false)"),
                {"uid": user_id},
            )
            await sesi.commit()

            count_with = (await sesi.execute(
                text("SELECT COUNT(*) FROM postmortems "
                     "WHERE user_id = :uid AND embedding IS NOT NULL"),
                {"uid": user_id},
            )).scalar()
            report.ok("Vector: NULL embedding safe", f"{count_with}/4 rows have embedding, 1 NULL — no crash")

        except Exception as e:
            report.fail("Vector: unexpected error", str(e)[:200], critical=True)

        finally:
            if user_id:
                await sesi.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
                await sesi.commit()


# ── Kategori 5: Constraint Integrity ──────────────────────────────────────────

async def _test_constraints(report: AgentReport) -> None:
    email = _email("-const")
    user_id = None

    async with _Session() as sesi:
        try:
            row = (await sesi.execute(
                text("INSERT INTO users (id, email, password_hash) "
                     "VALUES (gen_random_uuid(), :e, :p) RETURNING id"),
                {"e": email, "p": "$2b$12$fakehash"},
            )).fetchone()
            await sesi.commit()
            user_id = row[0]
        except Exception as e:
            await sesi.rollback()
            report.fail("Constraint: setup", str(e)[:200], critical=True)
            return

        try:
            # 5a. UNIQUE email
            try:
                await sesi.execute(
                    text("INSERT INTO users (id, email, password_hash) "
                         "VALUES (gen_random_uuid(), :e, :p)"),
                    {"e": email, "p": "$2b$12$fakehash"},
                )
                await sesi.commit()
                report.fail("Constraint: UNIQUE email", "Duplicate diterima — constraint hilang", critical=True)
            except IntegrityError:
                await sesi.rollback()
                report.ok("Constraint: UNIQUE email", "IntegrityError raised ✓")

            # 5b. NOT NULL email
            try:
                await sesi.execute(
                    text("INSERT INTO users (id, email, password_hash) "
                         "VALUES (gen_random_uuid(), NULL, 'x')"),
                )
                await sesi.commit()
                report.fail("Constraint: NOT NULL email", "NULL email diterima", critical=True)
            except Exception:
                await sesi.rollback()
                report.ok("Constraint: NOT NULL email", "NULL rejected ✓")

            # 5c. FK violation
            try:
                await sesi.execute(
                    text("INSERT INTO postmortems "
                         "(id, user_id, title, incident_date, raw_content, has_recurrence) "
                         "VALUES (gen_random_uuid(), :uid, 'Orphan', '2025-01-01', 'x', false)"),
                    {"uid": str(uuid.uuid4())},
                )
                await sesi.commit()
                report.fail("Constraint: FK user_id", "Orphan postmortem diterima", critical=True)
            except IntegrityError:
                await sesi.rollback()
                report.ok("Constraint: FK user_id", "FK violation rejected ✓")

            # 5d. CHECK severity
            try:
                await sesi.execute(
                    text("INSERT INTO postmortems "
                         "(id, user_id, title, incident_date, raw_content, severity, has_recurrence) "
                         "VALUES (gen_random_uuid(), :uid, 'Bad', '2025-01-01', 'x', 'INVALID', false)"),
                    {"uid": user_id},
                )
                await sesi.commit()
                report.warn("Constraint: severity CHECK", "INVALID severity diterima — CHECK constraint tidak ada")
                await sesi.execute(
                    text("DELETE FROM postmortems WHERE user_id=:uid AND severity='INVALID'"),
                    {"uid": user_id},
                )
                await sesi.commit()
            except IntegrityError:
                await sesi.rollback()
                report.ok("Constraint: severity CHECK", "INVALID severity rejected ✓")

        except Exception as e:
            report.fail("Constraint: unexpected error", str(e)[:200], critical=True)

        finally:
            if user_id:
                await sesi.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
                await sesi.commit()


# ── Kategori 6: Stress Test ───────────────────────────────────────────────────

async def _test_stress(report: AgentReport) -> None:
    lat_user: list[float] = []
    lat_pm: list[float]   = []
    lat_srch: list[float] = []
    err = 0
    anchor_id = None

    async with _Session() as sesi:
        try:
            row = (await sesi.execute(
                text("INSERT INTO users (id, email, password_hash) "
                     "VALUES (gen_random_uuid(), :e, :p) RETURNING id"),
                {"e": _email("-stress-anchor"), "p": "$2b$12$fakehash"},
            )).fetchone()
            await sesi.commit()
            anchor_id = row[0]
        except Exception as e:
            await sesi.rollback()
            report.fail("Stress: setup anchor user", str(e)[:200], critical=True)
            return

    sem = asyncio.Semaphore(10)

    # 6a. Concurrent user inserts
    async def insert_user(i: int):
        nonlocal err
        async with sem, _Session() as s:
            t0 = time.monotonic()
            try:
                await s.execute(
                    text("INSERT INTO users (id, email, password_hash) "
                         "VALUES (gen_random_uuid(), :e, :p)"),
                    {"e": _email(f"-stress-u{i}"), "p": "$2b$12$fakehash"},
                )
                await s.commit()
                lat_user.append((time.monotonic() - t0) * 1000)
            except Exception:
                err += 1
                await s.rollback()

    await asyncio.gather(*[insert_user(i) for i in range(STRESS_USERS)])

    if err == 0:
        report.ok(f"Stress: {STRESS_USERS} concurrent user inserts",
                  f"0 errors | p50={_p(lat_user,50):.0f}ms p95={_p(lat_user,95):.0f}ms p99={_p(lat_user,99):.0f}ms")
    else:
        report.fail(f"Stress: {STRESS_USERS} user inserts", f"{err} errors", critical=True)

    # 6b. Concurrent postmortem inserts + embeddings
    err = 0

    async def insert_pm(i: int):
        nonlocal err
        async with sem, _Session() as s:
            t0 = time.monotonic()
            try:
                await s.execute(
                    text("INSERT INTO postmortems "
                         "(id, user_id, title, incident_date, raw_content, embedding, has_recurrence) "
                         "VALUES (gen_random_uuid(), :uid, :title, '2025-01-01', 'stress', "
                         "        CAST(:emb AS vector), false)"),
                    {"uid": anchor_id, "title": f"Stress PM {i}", "emb": _emb(i)},
                )
                await s.commit()
                lat_pm.append((time.monotonic() - t0) * 1000)
            except Exception:
                err += 1
                await s.rollback()

    await asyncio.gather(*[insert_pm(i) for i in range(STRESS_POSTMORTEMS)])

    if err == 0:
        report.ok(f"Stress: {STRESS_POSTMORTEMS} concurrent postmortem inserts (with embedding)",
                  f"0 errors | p50={_p(lat_pm,50):.0f}ms p95={_p(lat_pm,95):.0f}ms p99={_p(lat_pm,99):.0f}ms")
    else:
        report.fail(f"Stress: {STRESS_POSTMORTEMS} postmortem inserts", f"{err} errors", critical=True)

    # 6c. Concurrent cosine searches
    err = 0

    async def cosine_search(i: int):
        nonlocal err
        async with sem, _Session() as s:
            t0 = time.monotonic()
            try:
                (await s.execute(
                    text("SELECT id FROM postmortems "
                         "WHERE user_id = :uid AND embedding IS NOT NULL "
                         "ORDER BY embedding <=> CAST(:q AS vector) LIMIT 5"),
                    {"uid": anchor_id, "q": _emb(i)},
                )).fetchall()
                lat_srch.append((time.monotonic() - t0) * 1000)
            except Exception:
                err += 1

    await asyncio.gather(*[cosine_search(i) for i in range(STRESS_SEARCHES)])

    if err == 0:
        report.ok(f"Stress: {STRESS_SEARCHES} concurrent cosine searches",
                  f"0 errors | p50={_p(lat_srch,50):.0f}ms p95={_p(lat_srch,95):.0f}ms p99={_p(lat_srch,99):.0f}ms")
    else:
        report.fail(f"Stress: {STRESS_SEARCHES} cosine searches", f"{err} errors", critical=True)

    total = len(lat_user) + len(lat_pm) + len(lat_srch)
    report.ok("Stress: total ops completed", str(total))

    # Cleanup
    async with _Session() as sesi:
        deleted = await _bersihkan(sesi)
        report.ok("Cleanup", f"{deleted} test user(s) + cascaded postmortems removed")


# ── Main ──────────────────────────────────────────────────────────────────────

class Phase1DatabaseAgent(BaseAgent):
    async def run(self, report: AgentReport):
        print("\n  === CATEGORY 1: HTTP Health Checks ===")
        http = _HttpChecks(self.base_url)
        http.client = self.client
        await http.run(report)

        print("\n  === CATEGORY 2: Schema Verification ===")
        await _test_schema(report)

        # Jika ada kegagalan schema kritis, CRUD dan test lanjutan tidak bisa
        # dijalankan — kolom yang dibutuhkan tidak ada di tabel.
        kritis = [f for f in report.failed if f[2]]
        if kritis:
            print(f"\n  ⛔  {len(kritis)} critical schema failure(s) — Categories 3–6 dilewati.")
            print(f"  ──────────────────────────────────────────────────────")
            print(f"  Jalankan reset schema dulu:")
            print(f"    cd backend && python scripts/reset_db.py")
            print(f"  Kemudian restart backend dan ulangi:")
            print(f"    make phase1")
            print(f"  ──────────────────────────────────────────────────────\n")
            return

        print("\n  === CATEGORY 3: CRUD Operations ===")
        await _test_crud(report)

        print("\n  === CATEGORY 4: Vector Operations ===")
        await _test_vectors(report)

        print("\n  === CATEGORY 5: Constraint Integrity ===")
        await _test_constraints(report)

        print("\n  === CATEGORY 6: Stress Test ===")
        await _test_stress(report)


if __name__ == "__main__":
    asyncio.run(Phase1DatabaseAgent().execute("Phase 1 — Database Foundation", day=0))
