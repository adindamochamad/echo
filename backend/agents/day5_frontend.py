from agents.base_agent import BaseAgent, AgentReport
import asyncio

REQUIRED_LANDING_FIELDS = ["similarity_score", "unimplemented_items", "echo_verdict", "days_between"]
REQUIRED_INCIDENT_FIELDS = ["id", "title", "incident_date", "severity", "summary", "root_causes", "action_items"]
REQUIRED_SCORE_FIELDS = ["score", "total_postmortems", "total_recurrences", "recurrence_rate", "avg_action_completion"]

class Day5FrontendAgent(BaseAgent):
    async def run(self, report: AgentReport):

        r = await self.get("/api/v1/demo/climax")
        if r.status_code == 200:
            data = r.json()
            missing = [f for f in REQUIRED_LANDING_FIELDS if f not in data]
            if not missing:
                report.ok("Landing page data shape", "All required fields present")
            else:
                report.fail("Landing page data shape", f"Missing: {missing}", critical=True)
            items = data.get("unimplemented_items", [])
            if items:
                item = items[0]
                item_fields = ["description", "owner", "status"]
                missing_item = [f for f in item_fields if f not in item]
                if not missing_item:
                    report.ok("Unimplemented item shape", "description, owner, status present")
                else:
                    report.fail("Unimplemented item shape", f"Missing: {missing_item}", critical=True)
        else:
            report.fail("Landing page data", f"HTTP {r.status_code}", critical=True)

        r = await self.get("/api/v1/demo/incidents")
        if r.status_code == 200:
            items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
            if items:
                missing = [f for f in REQUIRED_INCIDENT_FIELDS if f not in items[0]]
                if not missing:
                    report.ok("Incident list shape", f"{len(items)} items, all fields present")
                else:
                    report.fail("Incident list shape", f"Missing: {missing}", critical=True)
        else:
            report.fail("Incident list", f"HTTP {r.status_code}", critical=True)

        r = await self.get("/api/v1/demo/pattern-score")
        if r.status_code == 200:
            data = r.json()
            missing = [f for f in REQUIRED_SCORE_FIELDS if f not in data]
            if not missing:
                report.ok("Pattern score shape", "All fields present")
                score = data.get("score", -1)
                if 0 <= score <= 100:
                    report.ok("Score range", f"{score}/100 (valid 0-100 range)")
                else:
                    report.fail("Score range", f"Score {score} out of 0-100 range", critical=True)
            else:
                report.fail("Pattern score shape", f"Missing: {missing}", critical=True)
        else:
            report.fail("Pattern score", f"HTTP {r.status_code}", critical=True)

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": "Database service failed causing payment timeouts for 2 hours. No monitoring was configured. Root cause: connection pool exhausted. Action: add alerts."})
        if r.status_code == 200:
            data = r.json()
            frontend_fields = ["summary", "root_causes", "action_items", "severity", "recurrence_matches"]
            missing = [f for f in frontend_fields if f not in data]
            if not missing:
                report.ok("Demo analyze shape", "All frontend fields present")
            else:
                report.fail("Demo analyze shape", f"Missing: {missing}", critical=True)
        else:
            report.fail("Demo analyze", f"HTTP {r.status_code}", critical=True)

        r = await self.client.options(
            f"{self.base_url}/api/v1/demo/climax",
            headers={"Origin": "https://echo-app.vercel.app", "Access-Control-Request-Method": "GET"}
        )
        cors_header = r.headers.get("access-control-allow-origin", "")
        if cors_header:
            report.ok("CORS for Vercel", f"Allow-Origin: {cors_header}")
        else:
            report.warn("CORS for Vercel", "No CORS header for Vercel domain — may break in production")

        import time
        endpoints = [
            "/api/v1/demo/incidents",
            "/api/v1/demo/climax",
            "/api/v1/demo/pattern-score",
        ]
        for ep in endpoints:
            start = time.time()
            await self.get(ep)
            ms = (time.time() - start) * 1000
            if ms < 500:
                report.ok(f"Response time {ep}", f"{ms:.0f}ms")
            elif ms < 2000:
                report.warn(f"Response time {ep}", f"{ms:.0f}ms — acceptable but slow")
            else:
                report.fail(f"Response time {ep}", f"{ms:.0f}ms — too slow for smooth demo", critical=False)

if __name__ == "__main__":
    agent = Day5FrontendAgent()
    asyncio.run(agent.execute("Frontend UX Agent", day=5))
