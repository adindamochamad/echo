from agents.base_agent import BaseAgent, AgentReport
import asyncio, json

TEST_POSTMORTEMS = [
    {
        "name": "Standard P0 incident",
        "text": """
        Payment service went down on Friday at 2pm. Root cause was database
        connection pool exhausted — max_connections was set to 20, not reviewed
        since initial deploy. No alerts fired. Duration: 4 hours 23 minutes.
        Action items: increase max_connections to 100, add PagerDuty alert for
        pool utilization > 80%, implement retry with backoff in payment-service.
        Owner: Sarah Kim for monitoring, Marcus Reid for retry logic.
        """,
        "expected_severity": "P0",
        "expected_systems": ["payment-service"],
        "min_root_causes": 1,
        "min_action_items": 2,
    },
    {
        "name": "Minimal incident notes",
        "text": """
        Auth service went down for 2 hours. Memory leak. Fixed by restart.
        Need to find root cause. On call was paged at 3am.
        """,
        "expected_severity": None,
        "min_root_causes": 1,
        "min_action_items": 1,
    },
    {
        "name": "Non-English incident (Bahasa Indonesia)",
        "text": """
        Layanan pembayaran mengalami gangguan selama 3 jam pada hari Senin.
        Penyebab utama: koneksi database habis karena konfigurasi pool yang tidak diperbarui.
        Item tindakan: perbarui konfigurasi pool database, tambahkan monitoring.
        Pemilik: Tim infrastruktur. Tingkat keparahan: P1.
        """,
        "expected_severity": None,
        "min_root_causes": 1,
        "min_action_items": 1,
    },
]

class Day2ExtractionAgent(BaseAgent):
    async def run(self, report: AgentReport):

        for test in TEST_POSTMORTEMS:
            name = test["name"]
            print(f"\n  Testing: {name}")

            try:
                r = await self.post("/api/v1/demo/analyze", json={"raw_content": test["text"].strip()})

                if r.status_code != 200:
                    report.fail(f"{name} — API call", f"HTTP {r.status_code}: {r.text[:100]}", critical=True)
                    continue

                data = r.json()

                required = ["summary", "root_causes", "action_items", "severity", "systems_affected"]
                missing = [f for f in required if f not in data]
                if missing:
                    report.fail(f"{name} — Required fields", f"Missing: {missing}", critical=True)
                    continue
                report.ok(f"{name} — Fields present")

                summary = data.get("summary", "")
                if len(summary) > 30:
                    report.ok(f"{name} — Summary quality", f"{len(summary)} chars")
                else:
                    report.fail(f"{name} — Summary quality", f"Too short: '{summary}'", critical=False)

                rc = data.get("root_causes", [])
                if len(rc) >= test["min_root_causes"]:
                    report.ok(f"{name} — Root causes", f"{len(rc)} extracted")
                else:
                    report.fail(f"{name} — Root causes", f"Only {len(rc)}, expected >= {test['min_root_causes']}", critical=True)

                generic_rc = [r for r in rc if r.lower().startswith(("lack of", "insufficient", "poor", "missing"))]
                if generic_rc:
                    report.warn(f"{name} — Root cause specificity", f"Generic phrases detected: {generic_rc[:1]}")
                else:
                    report.ok(f"{name} — Root cause specificity", "No generic 'lack of X' patterns")

                ai = data.get("action_items", [])
                if len(ai) >= test["min_action_items"]:
                    report.ok(f"{name} — Action items", f"{len(ai)} extracted")
                else:
                    report.fail(f"{name} — Action items", f"Only {len(ai)}, expected >= {test['min_action_items']}", critical=True)

                incomplete_ai = [a for a in ai if len(a.get("description", "")) < 15]
                if incomplete_ai:
                    report.warn(f"{name} — Action item quality", f"{len(incomplete_ai)} items have vague descriptions")
                else:
                    report.ok(f"{name} — Action item quality", "All descriptions are specific")

                severity = data.get("severity", "")
                if test.get("expected_severity") and severity == test["expected_severity"]:
                    report.ok(f"{name} — Severity", severity)
                elif severity in ["P0", "P1", "P2", "P3"]:
                    report.ok(f"{name} — Severity detected", severity)
                else:
                    report.warn(f"{name} — Severity", f"Got '{severity}' — expected P0/P1/P2/P3")

            except Exception as e:
                report.fail(f"{name} — Exception", str(e), critical=True)

        print("\n  Testing: Rate limiting")
        for i in range(6):
            try:
                r = await self.post("/api/v1/demo/analyze", json={"raw_content": "Test " * 10})
                if i < 5 and r.status_code == 200:
                    pass
                elif i >= 5 and r.status_code == 429:
                    report.ok("Rate limiting", "429 returned after 5 requests")
                    break
            except Exception as e:
                report.warn("Rate limiting", str(e))
                break

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": ""})
        if r.status_code == 422:
            report.ok("Empty content rejected", "422 validation error")
        else:
            report.fail("Empty content rejected", f"Got {r.status_code}, expected 422", critical=True)

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": "short"})
        if r.status_code == 422:
            report.ok("Too short rejected", "422 for content < 50 chars")
        else:
            report.fail("Too short rejected", f"Got {r.status_code}", critical=True)

if __name__ == "__main__":
    agent = Day2ExtractionAgent()
    asyncio.run(agent.execute("Extraction Quality Agent", day=2))
