from agents.base_agent import BaseAgent, AgentReport
import asyncio, os

PROD_URL = os.getenv("ECHO_PROD_URL", "https://your-echo-backend.railway.app")
FRONTEND_URL = os.getenv("ECHO_FRONTEND_URL", "https://your-echo.vercel.app")

class Day8PreSubmitAgent(BaseAgent):
    async def run(self, report: AgentReport):
        print(f"  Target: {PROD_URL}")
        print(f"  Frontend: {FRONTEND_URL}\n")

        r = await self.get("/health")
        if r.status_code == 200 and r.json().get("status") == "ok":
            report.ok("Production health", "API running in production")
            if r.json().get("pgvector") == "enabled":
                report.ok("pgvector production", "Extension active")
            else:
                report.fail("pgvector production", "Not enabled in production", True)
        else:
            report.fail("Production health", f"HTTP {r.status_code}", True)

        demo_endpoints = [
            "/api/v1/demo/incidents",
            "/api/v1/demo/climax",
            "/api/v1/demo/pattern-score",
        ]
        for ep in demo_endpoints:
            r = await self.get(ep)
            if r.status_code == 200:
                report.ok(f"Production: {ep}", "200 OK")
            else:
                report.fail(f"Production: {ep}", f"HTTP {r.status_code}", True)

        r = await self.post("/api/v1/demo/analyze", json={
            "raw_content": "Database connection pool exhausted during peak traffic. Payment service down for 3 hours. No monitoring configured. Root cause: max_connections=20 not reviewed. Action: increase limits, add alerting."
        })
        if r.status_code == 200:
            data = r.json()
            if data.get("root_causes"):
                report.ok("Production extraction", "Claude API working in production")
            else:
                report.fail("Production extraction", "Empty extraction — Claude API may be misconfigured", True)
        else:
            report.fail("Production submission", f"HTTP {r.status_code}", True)

        import time
        for ep in ["/health", "/api/v1/demo/climax"]:
            start = time.time()
            await self.get(ep)
            ms = (time.time() - start) * 1000
            if ms < 1000:
                report.ok(f"Prod response time {ep}", f"{ms:.0f}ms")
            elif ms < 3000:
                report.warn(f"Prod response time {ep}", f"{ms:.0f}ms — acceptable")
            else:
                report.fail(f"Prod response time {ep}", f"{ms:.0f}ms — too slow for demo", False)

        r = await self.client.options(
            f"{PROD_URL}/api/v1/demo/climax",
            headers={"Origin": FRONTEND_URL, "Access-Control-Request-Method": "GET"}
        )
        cors = r.headers.get("access-control-allow-origin", "")
        if cors:
            report.ok("Production CORS", f"Allows: {cors}")
        else:
            report.fail("Production CORS", f"No CORS for {FRONTEND_URL} — frontend calls will fail", True)

        r = await self.get("/health")
        text = r.text
        secrets = ["sk-ant-", "ANTHROPIC_API_KEY", "postgres://", "eyJ"]
        exposed = [s for s in secrets if s in text]
        if not exposed:
            report.ok("No secrets exposed", "Health endpoint clean")
        else:
            report.fail("Secrets exposed", f"Found in health: {exposed}", True)

        print(f"\n  {chr(9608)} MANUAL CHECKS (verify yourself):")
        manual = [
            "Open frontend URL in incognito — loads < 3 seconds",
            "Split screen demo visible WITHOUT scrolling on 1280x800",
            "RecurrenceAlert shows 3 unimplemented items with status badges",
            "ECHO verdict sentence visible: '...was preventable'",
            "Works on 375px width (Chrome DevTools mobile sim)",
            "Works in Firefox browser",
            "window.pendo.getVisitorId() returns string in console",
            "Novus dashboard screenshot taken and saved",
            "No placeholder text or TODO visible in UI",
            "All loading states show skeleton (not blank areas)",
        ]
        for item in manual:
            print(f"  [ ] {item}")

if __name__ == "__main__":
    agent = Day8PreSubmitAgent(PROD_URL)
    asyncio.run(agent.execute("Pre-Submit Final Agent", day=8))
