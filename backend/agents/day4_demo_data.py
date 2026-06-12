from agents.base_agent import BaseAgent, AgentReport
import asyncio

class Day4DemoDataAgent(BaseAgent):
    async def run(self, report: AgentReport):

        r = await self.get("/api/v1/demo/incidents")
        if r.status_code != 200:
            report.fail("Demo incidents endpoint", f"HTTP {r.status_code}", critical=True)
            return
        incidents = r.json()
        items = incidents if isinstance(incidents, list) else incidents.get("items", [])
        if len(items) >= 8:
            report.ok("Demo incident count", f"{len(items)} incidents seeded")
        else:
            report.fail("Demo incident count", f"Only {len(items)}/8 — run seed script", critical=True)

        dates = [i.get("incident_date", "") for i in items]
        dates_sorted = sorted(dates)
        if dates_sorted:
            report.ok("Date range", f"{dates_sorted[0]} → {dates_sorted[-1]}")
            if dates_sorted[0] < "2025-04-01" and dates_sorted[-1] > "2025-10-01":
                report.ok("Date spread", "Incidents span 7+ months — good for narrative")
            else:
                report.warn("Date spread", "Incidents may not span enough time for '8 months ago' narrative")

        severities = [i.get("severity", "unknown") for i in items]
        p0_count = severities.count("P0")
        if p0_count >= 2:
            report.ok("P0 incidents", f"{p0_count} P0 incidents (high stakes)")
        else:
            report.warn("P0 incidents", f"Only {p0_count} P0 — consider bumping severities for demo impact")

        score_r = await self.get("/api/v1/demo/pattern-score")
        if score_r.status_code == 200:
            score_data = score_r.json()
            recurrences = score_data.get("total_recurrences", 0)
            if recurrences >= 3:
                report.ok("Recurrence count", f"{recurrences} recurrences in demo org")
            else:
                report.fail("Recurrence count", f"Only {recurrences} — need >= 3 for demo narrative", critical=True)

        climax_r = await self.get("/api/v1/demo/climax")
        if climax_r.status_code == 200:
            climax = climax_r.json()
            title = climax.get("title", "")
            if "checkout" in title.lower() or "connection" in title.lower() or "november" in title.lower():
                report.ok("Climax incident", f"Correct: '{title[:60]}'")
            else:
                report.warn("Climax incident", f"Unexpected title: '{title}' — may not be the right incident")

            unimplemented = climax.get("unimplemented_items", [])
            never_started = [u for u in unimplemented if u.get("status") in ["NEVER STARTED", "never_started"]]
            abandoned = [u for u in unimplemented if u.get("status") in ["ABANDONED", "abandoned"]]
            if never_started or abandoned:
                report.ok("Unimplemented severity", f"{len(never_started)} NEVER STARTED + {len(abandoned)} ABANDONED — maximum impact")
            else:
                report.warn("Unimplemented severity", "No NEVER STARTED/ABANDONED items — reduce emotional impact of demo")

        r2 = await self.get("/api/v1/demo/incidents")
        items2 = r2.json() if isinstance(r2.json(), list) else r2.json().get("items", [])
        if len(items2) == len(items):
            report.ok("Seed idempotency", "No duplicate incidents")
        else:
            report.fail("Seed idempotency", f"Count changed: {len(items)} → {len(items2)}", critical=True)

if __name__ == "__main__":
    agent = Day4DemoDataAgent()
    asyncio.run(agent.execute("Demo Data Integrity Agent", day=4))
