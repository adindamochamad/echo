"""
Phase 4 — Demo Data Integrity Agent

Verifies:
  1. No hardcoded score constants (SIMILARITY_SCORE, PATTERN_SCORE, TOTAL_RECURRENCES removed)
  2. Demo incidents are diverse (not all about the same root cause)
  3. Pattern score is computed dynamically
  4. Similarity score is computed dynamically
  5. Unrelated incidents score low vs the DB pool recurrence pair
  6. Live endpoints return plausible computed values
"""

import asyncio
import sys

sys.path.insert(0, ".")

import httpx

from agents.base_agent import AgentReport


class Phase4DemoAgent:
    def __init__(self):
        self.report = AgentReport("Phase 4 — Demo Data Integrity", day=4)
        self.base_url = "http://localhost:8000"

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def get(self, path: str):
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/api/v1{path}")
            resp.raise_for_status()
            return resp.json()

    # ── Category 1: No hardcoded constants in source files ───────────────────

    def check_no_hardcoded_constants(self):
        import ast
        import os

        files_to_check = [
            "app/services/demo_data.py",
            "app/services/matching_service.py",
            "app/routers/demo.py",
        ]

        forbidden = {
            "SIMILARITY_SCORE": 0.91,
            "PATTERN_SCORE": 38,
            "TOTAL_RECURRENCES": 5,
        }

        for file_path in files_to_check:
            if not os.path.exists(file_path):
                self.report.fail(f"Source file not found: {file_path}")
                continue
            with open(file_path) as f:
                source = f.read()
            for name in forbidden:
                if f"{name} = " in source:
                    self.report.fail(f"{file_path}: still contains hardcoded '{name} ='")
                else:
                    self.report.ok(f"{file_path}: no hardcoded '{name}'")

        # Also verify _skor_boost_pola_db_pool is gone from matching_service
        with open("app/services/matching_service.py") as f:
            ms_source = f.read()
        if "_skor_boost_pola_db_pool" in ms_source:
            self.report.fail("matching_service.py: artificial boost function still present")
        else:
            self.report.ok("matching_service.py: artificial boost function removed")

    # ── Category 2: Incident diversity ───────────────────────────────────────

    def check_incident_diversity(self):
        from app.services.demo_data import DEMO_INCIDENTS

        if len(DEMO_INCIDENTS) < 8:
            self.report.fail(f"Expected 8 demo incidents, got {len(DEMO_INCIDENTS)}")
            return
        self.report.ok(f"Demo has {len(DEMO_INCIDENTS)} incidents")

        # All systems_affected across non-recurrence-pair incidents
        non_pair_ids = {i.id for i in DEMO_INCIDENTS if i.id not in ("inc-001", "inc-008")}
        all_systems = set()
        for inc in DEMO_INCIDENTS:
            if inc.id in non_pair_ids:
                all_systems.update(inc.systems_affected)

        # Must have systems beyond postgres/payment-service/checkout-service
        db_only_systems = {"postgres", "payment-service", "checkout-service", "database"}
        diverse_systems = all_systems - db_only_systems
        if len(diverse_systems) >= 3:
            self.report.ok(f"Incidents span {len(diverse_systems)} non-DB systems: {', '.join(sorted(diverse_systems)[:5])}")
        else:
            self.report.fail(f"Incidents still too DB-focused — diverse systems: {diverse_systems}")

        # Verify inc-001 and inc-008 are the only recurrences
        recurrence_ids = [i.id for i in DEMO_INCIDENTS if i.has_recurrence]
        if set(recurrence_ids) == {"inc-001", "inc-008"}:
            self.report.ok("Recurrence pair is exactly inc-001 and inc-008")
        else:
            self.report.warn(f"Unexpected recurrence IDs: {recurrence_ids} (expected inc-001, inc-008)")

        # Middle incidents (002-007) should all have has_recurrence=False
        middle = [i for i in DEMO_INCIDENTS if i.id not in ("inc-001", "inc-008")]
        bad = [i.id for i in middle if i.has_recurrence]
        if not bad:
            self.report.ok("Middle incidents (inc-002 to inc-007) correctly have has_recurrence=False")
        else:
            self.report.fail(f"Middle incidents incorrectly marked as recurrence: {bad}")

    # ── Category 3: Dynamic pattern score computation ─────────────────────────

    def check_dynamic_pattern_score(self):
        from app.services.demo_data import DEMO_INCIDENTS, hitung_pattern_score
        from app.schemas.demo import ActionItemStatus

        stats = hitung_pattern_score(DEMO_INCIDENTS)

        # Verify formula correctness manually
        total = len(DEMO_INCIDENTS)
        recurrences = sum(1 for i in DEMO_INCIDENTS if i.has_recurrence)
        all_items = [ai for inc in DEMO_INCIDENTS for ai in inc.action_items]
        completed = sum(1 for ai in all_items if ai.status == ActionItemStatus.COMPLETED)
        completion_rate = completed / len(all_items) if all_items else 0.0
        recurrence_rate = recurrences / total
        expected_score = round((1.0 - recurrence_rate) * 50 + completion_rate * 50)

        self.report.ok(
            f"Pattern score computed: {stats['score']}/100 "
            f"(recurrence_rate={recurrence_rate:.2f}, completion_rate={completion_rate:.2f})"
        )

        if stats["score"] == expected_score:
            self.report.ok(f"Pattern score formula verified: {stats['score']} matches expected {expected_score}")
        else:
            self.report.fail(f"Pattern score mismatch: got {stats['score']}, expected {expected_score}")

        # Score should be between 40-90 — honest range for a struggling team
        if 30 <= stats["score"] <= 90:
            self.report.ok(f"Pattern score {stats['score']} is in honest range [30, 90]")
        else:
            self.report.warn(f"Pattern score {stats['score']} outside expected honest range [30, 90]")

    # ── Category 4: Dynamic similarity score for climax pair ─────────────────

    def check_dynamic_similarity(self):
        from app.services.demo_data import (
            CLIMAX_CURRENT_ID, CLIMAX_MATCHED_ID, DEMO_INCIDENTS
        )
        from app.services.matching_service import hitung_skor_kemiripan

        def _text(inc) -> str:
            return " ".join(
                [inc.title, inc.summary] + inc.root_causes + inc.systems_affected
            )

        inc_current = next((i for i in DEMO_INCIDENTS if i.id == CLIMAX_CURRENT_ID), None)
        inc_lama = next((i for i in DEMO_INCIDENTS if i.id == CLIMAX_MATCHED_ID), None)

        if not inc_current or not inc_lama:
            self.report.fail("Could not find climax incidents for similarity check")
            return

        score = hitung_skor_kemiripan(_text(inc_current), inc_lama)
        self.report.ok(f"Computed similarity (inc-008 vs inc-001): {score:.4f}")

        if score > 0.91:
            self.report.fail(f"Similarity score {score:.4f} is suspiciously high — possible hardcoded boost remaining")
        elif score >= 0.40:
            self.report.ok(f"Score {score:.4f} is honest: clearly a match (>= 0.40 threshold) without artificial inflation")
        elif score >= 0.25:
            self.report.warn(f"Score {score:.4f} is low — still a valid weak match but may not look compelling in demo")
        else:
            self.report.fail(f"Score {score:.4f} is below 0.25 — recurrence pair won't be detected")

        # Verify an unrelated incident (CDN/auth) scores much lower vs inc-001
        inc_unrelated = next((i for i in DEMO_INCIDENTS if i.id == "inc-003"), None)
        if inc_unrelated:
            score_unrelated = hitung_skor_kemiripan(_text(inc_unrelated), inc_lama)
            self.report.ok(f"Unrelated incident inc-003 (CDN) vs inc-001 score: {score_unrelated:.4f}")
            if score_unrelated < score - 0.15:
                self.report.ok(f"Discrimination confirmed: recurrence pair scores {score:.2f} vs unrelated {score_unrelated:.2f} (Δ={score - score_unrelated:.2f})")
            else:
                self.report.warn(
                    f"Low discrimination: inc-003 scores {score_unrelated:.2f} vs inc-008's {score:.2f} — "
                    "matching may be too broad"
                )

    # ── Category 5: Live endpoint values ────────────────────────────────────

    async def check_live_endpoints(self):
        # Pattern score endpoint
        try:
            ps = await self.get("/demo/pattern-score")
            self.report.ok(f"GET /demo/pattern-score → score={ps['score']}, recurrences={ps['total_recurrences']}/{ps['total_postmortems']}")
            if ps["score"] > 95:
                self.report.fail(f"Pattern score {ps['score']} looks hardcoded/inflated (> 95)")
            elif ps["score"] == 38:
                self.report.fail("Pattern score is still the hardcoded value 38")
            else:
                self.report.ok(f"Pattern score {ps['score']} appears dynamically computed")
        except Exception as e:
            self.report.fail(f"GET /demo/pattern-score failed: {e}")

        # Climax endpoint
        try:
            climax = await self.get("/demo/climax")
            sim = climax.get("similarity_score", 0)
            self.report.ok(f"GET /demo/climax → similarity_score={sim}")
            if sim == 0.91:
                self.report.fail(f"Similarity score is still the hardcoded value 0.91")
            elif sim >= 0.40:
                self.report.ok(f"Similarity score {sim} is honest (>= 0.40 threshold)")
            else:
                self.report.warn(f"Similarity score {sim} < 0.40 — recurrence may not look compelling")
        except Exception as e:
            self.report.fail(f"GET /demo/climax failed: {e}")

        # Incidents endpoint — verify diversity
        try:
            incidents = await self.get("/demo/incidents")
            systems = set(s for i in incidents for s in i.get("systems_affected", []))
            self.report.ok(f"GET /demo/incidents → {len(incidents)} incidents, {len(systems)} unique systems: {', '.join(sorted(systems)[:6])}")
            non_db = {s for s in systems if s not in ("postgres", "payment-service", "checkout-service", "database")}
            if len(non_db) >= 3:
                self.report.ok(f"Diverse systems confirmed: {', '.join(sorted(non_db))}")
            else:
                self.report.fail(f"Still too DB-focused — non-DB systems: {non_db}")
        except Exception as e:
            self.report.fail(f"GET /demo/incidents failed: {e}")

    # ── Run all ───────────────────────────────────────────────────────────────

    async def run(self):
        print("\n=== Phase 4 — Demo Data Integrity ===\n")

        print("Category 1: No hardcoded constants")
        self.check_no_hardcoded_constants()

        print("\nCategory 2: Incident diversity")
        self.check_incident_diversity()

        print("\nCategory 3: Dynamic pattern score")
        self.check_dynamic_pattern_score()

        print("\nCategory 4: Dynamic similarity score")
        self.check_dynamic_similarity()

        print("\nCategory 5: Live endpoints")
        await self.check_live_endpoints()

        return self.report.print_summary()


if __name__ == "__main__":
    agent = Phase4DemoAgent()
    exit_code = asyncio.run(agent.run())
    sys.exit(exit_code)
