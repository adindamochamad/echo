"""
Demo incidents — 8 realistic incidents from different problem categories.

Narrative: inc-001 (March, DB pool) and inc-008 (November, DB pool cascade) are the
recurrence pair — same unfixed root cause, 8 months apart. The 6 middle incidents are
genuinely different failures, making the pattern detection non-trivial.
"""

from datetime import date

from app.schemas.demo import ActionItem, ActionItemStatus, IncidentSummary, Severity

DEMO_INCIDENTS: list[IncidentSummary] = [
    # ── inc-001: DB connection pool (the original) ───────────────────────────
    IncidentSummary(
        id="inc-001",
        title="Payment Service Outage — DB Connection Pool Exhaustion",
        incident_date="2025-03-15",
        severity=Severity.P0,
        summary="Payment service down 4h 23m. Root cause: max_connections=20 never reviewed since initial deploy in 2023. Pool saturated under normal load spike. No monitoring alert fired.",
        root_causes=[
            "Database connection pool max_connections=20 never increased since initial deployment",
            "No monitoring configured for pool utilization",
        ],
        action_items=[
            ActionItem(description="Increase max_connections to 100 in prod config", owner="Sarah Kim", status=ActionItemStatus.NEVER_STARTED),
            ActionItem(description="Add PagerDuty alert for pool utilization > 80%", owner="Sarah Kim", status=ActionItemStatus.ABANDONED),
            ActionItem(description="Implement exponential backoff in payment-service retry logic", owner="Marcus Reid", status=ActionItemStatus.NEVER_STARTED),
            ActionItem(description="Document connection pool sizing runbook", owner="DevOps", status=ActionItemStatus.COMPLETED),
        ],
        systems_affected=["payment-service", "postgres"],
        has_recurrence=True,
    ),

    # ── inc-002: Auth service OOM — completely different problem ─────────────
    IncidentSummary(
        id="inc-002",
        title="Auth Service OOM Kill — Unbounded Session Cache Growth",
        incident_date="2025-04-02",
        severity=Severity.P1,
        summary="Auth service restarted 3 times in 4 hours due to OOM kill. Root cause: in-memory session cache had no eviction policy — grew unboundedly over 72h until the OOM killer terminated the process.",
        root_causes=[
            "In-memory session cache in auth-service had no eviction policy",
            "No memory usage alerting or container memory limits configured",
        ],
        action_items=[
            ActionItem(description="Replace in-memory cache with Redis (eviction policy: allkeys-lru)", owner="Backend Team", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Add memory usage alert at 85% container limit", owner="DevOps", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Set resource limits in Kubernetes manifest", owner="DevOps", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Review all in-memory stores for bounded growth", owner="Backend Team", status=ActionItemStatus.OPEN),
        ],
        systems_affected=["auth-service"],
        has_recurrence=False,
    ),

    # ── inc-003: CDN stale assets — frontend / deploy issue ──────────────────
    IncidentSummary(
        id="inc-003",
        title="Stale CSS After Deploy — CDN Cache Not Invalidated",
        incident_date="2025-05-14",
        severity=Severity.P2,
        summary="After frontend deploy ~30% of users in APAC saw broken UI for 55 minutes. CloudFront invalidation was triggered but APAC edge propagation exceeded SLA. Content-hash filenames not yet adopted.",
        root_causes=[
            "CSS and JS assets deployed without content-hash filenames — CDN served stale version",
            "CDN invalidation SLA not documented per region; APAC propagation takes up to 60 minutes",
        ],
        action_items=[
            ActionItem(description="Switch all static assets to content-hashed filenames (webpack/vite)", owner="Frontend Team", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Add CDN purge step to deploy pipeline with per-region status check", owner="DevOps", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Document CDN propagation SLA per region in deploy runbook", owner="Frontend Team", status=ActionItemStatus.OPEN),
        ],
        systems_affected=["cdn", "frontend"],
        has_recurrence=False,
    ),

    # ── inc-004: Third-party API rate limit — external dependency ────────────
    IncidentSummary(
        id="inc-004",
        title="Stripe API Rate Limit — Checkout Payment Failures",
        incident_date="2025-06-18",
        severity=Severity.P1,
        summary="Checkout payment processing failed for 22 minutes after a subscription renewal batch job saturated Stripe API rate limits. No retry logic in the batch job; failed renewals were silently dropped.",
        root_causes=[
            "Subscription renewal batch job had no rate-limit awareness — fired all API calls concurrently",
            "No alert configured for Stripe API error rate or rate limit headers",
        ],
        action_items=[
            ActionItem(description="Add token-bucket rate limiting to batch renewal job", owner="Backend Team", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Alert on Stripe API error rate > 1% over 5 minutes", owner="DevOps", status=ActionItemStatus.NEVER_STARTED),
            ActionItem(description="Audit all third-party integrations for rate limit handling", owner="Backend Team", status=ActionItemStatus.COMPLETED),
        ],
        systems_affected=["checkout-service", "stripe-integration"],
        has_recurrence=False,
    ),

    # ── inc-005: Redis maxmemory — caching / session issue ───────────────────
    IncidentSummary(
        id="inc-005",
        title="Redis Maxmemory Reached — Mass Session Invalidation",
        incident_date="2025-07-30",
        severity=Severity.P1,
        summary="Redis hit maxmemory with no eviction policy set. New writes were rejected, causing silent session invalidation. 1,200 logged-in users were force-logged out over 35 minutes.",
        root_causes=[
            "Redis deployed without maxmemory or eviction policy — default rejects writes when full",
            "Session size grew significantly after user profile fields added in June release",
        ],
        action_items=[
            ActionItem(description="Set maxmemory-policy to allkeys-lru in Redis config", owner="DevOps", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Add Redis memory utilization alert at 75%", owner="DevOps", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Cap session payload size; move large fields to DB", owner="Backend Team", status=ActionItemStatus.COMPLETED),
        ],
        systems_affected=["redis", "auth-service", "session-store"],
        has_recurrence=False,
    ),

    # ── inc-006: Hot deploy without drain — rollout issue ────────────────────
    IncidentSummary(
        id="inc-006",
        title="Hot Deploy Without Connection Drain — Checkout Errors",
        incident_date="2025-08-20",
        severity=Severity.P1,
        summary="Checkout service deploy killed in-flight requests with no connection draining. 6 minutes of 502 errors while pods were replaced. Kubernetes rollingUpdate was configured but preStop hook was missing.",
        root_causes=[
            "Kubernetes deployment missing preStop lifecycle hook for graceful connection drain",
            "Deploy triggered at peak hour with no staging smoke test before production",
        ],
        action_items=[
            ActionItem(description="Add preStop lifecycle hook with 30s sleep to all service deployments", owner="DevOps", status=ActionItemStatus.OPEN),
            ActionItem(description="Enforce staging deploy and smoke test before production promotion", owner="Engineering Manager", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Update deploy runbook with drain procedure and timing", owner="DevOps", status=ActionItemStatus.COMPLETED),
        ],
        systems_affected=["checkout-service", "kubernetes"],
        has_recurrence=False,
    ),

    # ── inc-007: DB migration lock — different DB problem ────────────────────
    IncidentSummary(
        id="inc-007",
        title="Blocking Migration — Payment Processing Slowdown",
        incident_date="2025-10-14",
        severity=Severity.P0,
        summary="Adding an index to the payments table without CONCURRENTLY acquired an exclusive lock for 8 minutes during peak traffic. Payment processing p99 latency spiked to 12s. No checkout downtime but significant user impact.",
        root_causes=[
            "CREATE INDEX ran without CONCURRENTLY on a 40M-row payments table during business hours",
            "Migration was reviewed but locking behaviour on large tables was not flagged",
        ],
        action_items=[
            ActionItem(description="Add CREATE INDEX CONCURRENTLY lint check to CI migration review", owner="Backend Team", status=ActionItemStatus.COMPLETED),
            ActionItem(description="Require DBA sign-off for schema changes on tables >1M rows", owner="Engineering Manager", status=ActionItemStatus.OPEN),
            ActionItem(description="Schedule production migrations outside peak hours", owner="DevOps", status=ActionItemStatus.NEVER_STARTED),
        ],
        systems_affected=["postgres", "payment-service"],
        has_recurrence=False,
    ),

    # ── inc-008: DB connection pool again — THE RECURRENCE ───────────────────
    IncidentSummary(
        id="inc-008",
        title="Checkout Service Down — DB Connection Pool Timeout Cascade",
        incident_date="2025-11-08",
        severity=Severity.P0,
        summary="Checkout service timed out cascade-style during Black Friday traffic. Root cause: DB connection pool max_connections still at 20 — identical to the March incident. No pool utilization alert was ever implemented. Duration: 2h 51m.",
        root_causes=[
            "Connection pool max_connections still at 20 — action item from March incident never implemented",
            "No pool utilization alerting — also never implemented despite two previous assignments",
        ],
        action_items=[
            ActionItem(description="Increase max_connections to 200 immediately", owner="SRE", status=ActionItemStatus.OPEN),
            ActionItem(description="Implement pool utilization alert (critical action item from March)", owner="Sarah Kim", status=ActionItemStatus.OPEN),
            ActionItem(description="Add exponential backoff to all DB-touching services", owner="Marcus Reid", status=ActionItemStatus.OPEN),
        ],
        systems_affected=["checkout-service", "payment-service", "postgres"],
        has_recurrence=True,
    ),
]

# Demo narrative anchors
CLIMAX_MATCHED_ID = "inc-001"
CLIMAX_CURRENT_ID = "inc-008"


def _cari_insiden_by_id(id_insiden: str) -> IncidentSummary | None:
    for insiden in DEMO_INCIDENTS:
        if insiden.id == id_insiden:
            return insiden
    return None


def tanggal_insiden_sekarang_demo() -> str:
    insiden = _cari_insiden_by_id(CLIMAX_CURRENT_ID)
    return insiden.incident_date if insiden else "2025-11-08"


def hitung_hari_antar_insiden(tanggal_lama: str, tanggal_baru: str | None = None) -> int:
    if tanggal_baru is None:
        tanggal_baru = tanggal_insiden_sekarang_demo()
    try:
        t_lama = date.fromisoformat(tanggal_lama)
        t_baru = date.fromisoformat(tanggal_baru)
        return max(0, (t_baru - t_lama).days)
    except ValueError:
        return 0


def hitung_pattern_score(incidents: list[IncidentSummary]) -> dict:
    """
    Compute pattern score dynamically (0-100).
    Higher = healthier team: fewer recurrences + more completed action items.
    """
    total = len(incidents)
    if total == 0:
        return {"score": 100, "total_postmortems": 0, "total_recurrences": 0,
                "recurrence_rate": 0.0, "avg_action_completion": 1.0}

    recurrences = sum(1 for i in incidents if i.has_recurrence)
    all_items = [ai for inc in incidents for ai in inc.action_items]
    completed = sum(1 for ai in all_items if ai.status == ActionItemStatus.COMPLETED)
    completion_rate = completed / len(all_items) if all_items else 0.0
    recurrence_rate = recurrences / total

    score = round((1.0 - recurrence_rate) * 50 + completion_rate * 50)
    score = max(0, min(100, score))

    return {
        "score": score,
        "total_postmortems": total,
        "total_recurrences": recurrences,
        "recurrence_rate": round(recurrence_rate, 4),
        "avg_action_completion": round(completion_rate, 4),
    }


def buat_echo_verdict(insiden_lama: IncidentSummary) -> str:
    belum = [
        ai for ai in insiden_lama.action_items
        if ai.status.value in ("NEVER STARTED", "ABANDONED", "OPEN")
    ]
    total = len(insiden_lama.action_items)
    return (
        f"{len(belum)} of {total} action items from the "
        f"{insiden_lama.incident_date} incident were never completed. "
        f"This recurrence was preventable."
    )
