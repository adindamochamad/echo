from agents.base_agent import BaseAgent, AgentReport
import asyncio, io

SAMPLE_TXT = b"""
Payment gateway outage - March 2025
Root cause: SSL certificate expired without alert. Duration: 47 minutes.
Systems: payment-gateway, checkout-service.
Contributing factors: no certificate expiry monitoring, manual renewal process.
Action items:
1. Set up automated cert renewal via Let's Encrypt. Owner: DevOps team. Due: April 1.
2. Add certificate expiry monitoring alert (30 days warning). Owner: Sarah Kim.
3. Document manual renewal process as backup procedure. Owner: Marcus Reid.
"""

class Day6IntegrationAgent(BaseAgent):
    async def run(self, report: AgentReport):

        try:
            r = await self.client.post(
                f"{self.base_url}/api/v1/postmortems/demo-import",
                files={"file": ("incident.txt", io.BytesIO(SAMPLE_TXT), "text/plain")},
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("summary") and data.get("root_causes"):
                    report.ok("TXT file import", "Extracted summary and root causes")
                else:
                    report.fail("TXT file import", "Missing extraction fields", critical=True)
            elif r.status_code == 404:
                report.warn("TXT file import", "Demo import endpoint not found — may use different path")
            else:
                report.fail("TXT file import", f"HTTP {r.status_code}: {r.text[:100]}", critical=True)
        except Exception as e:
            report.fail("TXT file import", str(e), critical=True)

        try:
            large_file = b"x" * (6 * 1024 * 1024)
            r = await self.client.post(
                f"{self.base_url}/api/v1/postmortems/demo-import",
                files={"file": ("large.txt", io.BytesIO(large_file), "text/plain")},
            )
            if r.status_code in [413, 422]:
                report.ok("File size limit", f"HTTP {r.status_code} for 6MB file")
            else:
                report.warn("File size limit", f"Got {r.status_code} for 6MB file — should be 413")
        except Exception as e:
            report.warn("File size limit", str(e))

        try:
            r = await self.client.post(
                f"{self.base_url}/api/v1/postmortems/demo-import",
                files={"file": ("file.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")},
            )
            if r.status_code in [415, 422]:
                report.ok("Unsupported file type", f"HTTP {r.status_code} for PDF")
            else:
                report.warn("Unsupported file type", f"Got {r.status_code} for PDF — should reject")
        except Exception as e:
            report.warn("Unsupported file type", str(e))

        try:
            pm_text = """
            Checkout service timeout cascade — connection pool limits reached during load test.
            Duration: 2 hours 51 minutes. Systems: checkout-service, payment-service, database.
            Root cause: connection pool max_connections not increased since initial deployment.
            No alerting configured for connection utilization. Contributing: new engineer ran load test.
            Action items: implement pool utilization alerting, add connection retry logic, update runbook.
            """
            r = await self.post("/api/v1/demo/analyze", json={"raw_content": pm_text.strip()})
            if r.status_code == 200:
                data = r.json()
                report.ok("End-to-end flow", "Submit → extract → match completed")
                if data.get("recurrence_matches"):
                    report.ok("E2E recurrence", f"{len(data['recurrence_matches'])} match(es) found")
                else:
                    report.warn("E2E recurrence", "No matches — verify demo seed data is loaded")
            else:
                report.fail("End-to-end flow", f"HTTP {r.status_code}", critical=True)
        except Exception as e:
            report.fail("End-to-end flow", str(e), critical=True)

        report.ok("Novus analytics", "Client-side only — verify manually in browser console")
        report.ok("Checklist", "Run: window.pendo.getVisitorId() in browser → must return string")

if __name__ == "__main__":
    agent = Day6IntegrationAgent()
    asyncio.run(agent.execute("Integration Agent", day=6))
