from agents.base_agent import BaseAgent, AgentReport
import asyncio, sys

class Day1InfraAgent(BaseAgent):
    async def run(self, report: AgentReport):

        # TEST 1: Health endpoint
        try:
            r = await self.get("/health")
            if r.status_code == 200:
                data = r.json()
                report.ok("Health endpoint", f"status={data.get('status')}")
                if data.get("pgvector") == "enabled":
                    report.ok("pgvector enabled", "Extension active in PostgreSQL")
                else:
                    report.fail("pgvector enabled", "pgvector not detected in health response", critical=True)
            else:
                report.fail("Health endpoint", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("Health endpoint", f"Connection refused: {e}", critical=True)

        # TEST 2: API prefix correct
        try:
            r = await self.get("/api/v1/health")
            report.ok("API v1 prefix", "Routes registered under /api/v1") if r.status_code != 404 else report.warn("API v1 prefix", "May not be configured")
        except Exception as e:
            report.warn("API v1 prefix", str(e))

        # TEST 3: CORS headers present
        try:
            r = await self.get("/health", headers={"Origin": "http://localhost:3000"})
            cors = r.headers.get("access-control-allow-origin", "")
            if cors:
                report.ok("CORS configured", f"Allow-Origin: {cors}")
            else:
                report.fail("CORS configured", "No CORS headers — frontend will be blocked", critical=True)
        except Exception as e:
            report.warn("CORS check", str(e))

        # TEST 4: GZip middleware
        try:
            r = await self.get("/health", headers={"Accept-Encoding": "gzip"})
            if "gzip" in r.headers.get("content-encoding", ""):
                report.ok("GZip compression", "Responses compressed")
            else:
                report.warn("GZip compression", "Not enabled — add GZipMiddleware to main.py")
        except Exception:
            report.warn("GZip check", "Could not verify")

        # TEST 5: Database connection
        try:
            # Try demo endpoint which requires DB
            r = await self.get("/api/v1/demo/incidents")
            if r.status_code in [200, 404]:
                report.ok("Database connection", "DB accessible via demo endpoint")
            elif r.status_code == 500:
                report.fail("Database connection", "500 error — DB may be misconfigured", critical=True)
        except Exception as e:
            report.fail("Database connection", str(e), critical=True)

        # TEST 6: Response time baseline
        import time
        try:
            start = time.time()
            await self.get("/health")
            elapsed = (time.time() - start) * 1000
            if elapsed < 200:
                report.ok("Response time", f"{elapsed:.0f}ms (target: <200ms)")
            else:
                report.warn("Response time", f"{elapsed:.0f}ms — slow for health check")
        except Exception:
            pass

if __name__ == "__main__":
    agent = Day1InfraAgent()
    asyncio.run(agent.execute("Infrastructure Validator", day=1))
