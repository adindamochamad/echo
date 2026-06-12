from agents.base_agent import BaseAgent, AgentReport
import asyncio

class Day3MatchingAgent(BaseAgent):
    async def run(self, report: AgentReport):

        try:
            r = await self.get("/api/v1/demo/climax")
            if r.status_code == 200:
                data = r.json()
                report.ok("Demo climax endpoint", "Returns 200")

                score = data.get("similarity_score", 0)
                if score > 0.80:
                    report.ok("Similarity score", f"{score:.2f} (target: >0.80)")
                else:
                    report.fail("Similarity score", f"{score:.2f} — too low, target >0.80", critical=True)

                unimplemented = data.get("unimplemented_items", [])
                if len(unimplemented) >= 2:
                    report.ok("Unimplemented items", f"{len(unimplemented)} items returned")
                else:
                    report.fail("Unimplemented items", f"Only {len(unimplemented)} — need >= 2 for demo impact", critical=True)

                verdict = data.get("echo_verdict", "")
                if verdict and len(verdict) > 20:
                    report.ok("ECHO verdict", f"Present: '{verdict[:60]}...'")
                else:
                    report.fail("ECHO verdict", "Missing or too short — this is the key demo sentence", critical=True)

                days_between = data.get("days_between", 0)
                if days_between > 100:
                    report.ok("Days between", f"{days_between} days (demo narrative: 8 months)")
                else:
                    report.warn("Days between", f"Only {days_between} days — demo narrative needs 200+ days")

            else:
                report.fail("Demo climax endpoint", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("Demo climax endpoint", str(e), critical=True)

        try:
            r = await self.get("/api/v1/demo/incidents")
            if r.status_code == 200:
                incidents = r.json()
                count = len(incidents) if isinstance(incidents, list) else len(incidents.get("items", []))
                if count >= 6:
                    report.ok("Demo incidents", f"{count} incidents seeded")
                else:
                    report.fail("Demo incidents", f"Only {count} — need >= 6 for rich demo", critical=False)
            else:
                report.fail("Demo incidents", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("Demo incidents", str(e), critical=True)

        try:
            r = await self.get("/api/v1/demo/pattern-score")
            if r.status_code == 200:
                data = r.json()
                score = data.get("score", 100)
                if score < 45:
                    report.ok("Pattern score", f"{score}/100 (Critical range — correct for demo)")
                else:
                    report.warn("Pattern score", f"{score}/100 — too high for demo narrative (target: <40)")
                recurrence_rate = data.get("recurrence_rate", 0)
                if recurrence_rate > 0.2:
                    report.ok("Recurrence rate", f"{recurrence_rate:.1%}")
                else:
                    report.warn("Recurrence rate", f"{recurrence_rate:.1%} — low, check seed data")
            else:
                report.fail("Pattern score", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("Pattern score", str(e), critical=True)

        try:
            similar_pm = """
            Database connection limits hit during load testing.
            Our checkout service cascaded failures to payment service due to connection timeouts.
            No monitoring was configured for database connection pool utilization.
            Duration: 2 hours 51 minutes. Systems: checkout-service, database.
            Action items: implement connection pool monitoring, add retry logic.
            """
            r = await self.post("/api/v1/demo/analyze", json={"raw_content": similar_pm.strip()})
            if r.status_code == 200:
                data = r.json()
                matches = data.get("recurrence_matches", [])
                if matches and len(matches) > 0:
                    top_score = matches[0].get("similarity_score", 0)
                    report.ok("Recurrence detection", f"Similar incident matched with score {top_score:.2f}")
                else:
                    report.warn("Recurrence detection", "No matches found for obviously similar incident — check matching logic")
            else:
                report.fail("Recurrence detection", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("Recurrence detection", str(e), critical=True)

        try:
            unrelated_pm = """
            Marketing website had a CSS rendering bug in Internet Explorer 11.
            Images were not displaying correctly for 2% of users.
            Fix: updated CSS vendor prefixes. Duration: 4 hours.
            Action items: set up cross-browser testing in CI pipeline.
            """
            r = await self.post("/api/v1/demo/analyze", json={"raw_content": unrelated_pm.strip()})
            if r.status_code == 200:
                data = r.json()
                matches = data.get("recurrence_matches", [])
                high_matches = [m for m in matches if m.get("similarity_score", 0) > 0.70]
                if not high_matches:
                    report.ok("False positive check", "No spurious matches for unrelated incident")
                else:
                    report.warn("False positive check", f"{len(high_matches)} high-score matches for unrelated incident — may be over-matching")
        except Exception as e:
            report.warn("False positive check", str(e))

if __name__ == "__main__":
    agent = Day3MatchingAgent()
    asyncio.run(agent.execute("Matching Intelligence Agent", day=3))
