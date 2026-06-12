from agents.base_agent import BaseAgent, AgentReport
import asyncio, io, json

class Day7ChaosAgent(BaseAgent):
    async def run(self, report: AgentReport):

        print("\n  === CATEGORY 1: Input Chaos ===")
        await self._test_input_chaos(report)

        print("\n  === CATEGORY 2: Boundary Conditions ===")
        await self._test_boundaries(report)

        print("\n  === CATEGORY 3: Auth & Security ===")
        await self._test_auth_security(report)

        print("\n  === CATEGORY 4: Concurrent Load ===")
        await self._test_concurrent(report)

        print("\n  === CATEGORY 5: Data Integrity ===")
        await self._test_data_integrity(report)

        print("\n  === CATEGORY 6: Demo Stability ===")
        await self._test_demo_stability(report)

    async def _test_input_chaos(self, report):
        r = await self.post("/api/v1/demo/analyze", json={})
        report.ok("Empty body → 422") if r.status_code == 422 else report.fail("Empty body", f"Got {r.status_code}", True)

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": "     \n\t  "})
        report.ok("Whitespace only → 422") if r.status_code == 422 else report.fail("Whitespace only", f"Got {r.status_code}", True)

        suffix = " database failure occurred affecting payment service requiring investigation."
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": "A" * (20000 - len(suffix)) + suffix})
        report.ok("Max length (20000) → 200") if r.status_code == 200 else report.fail("Max length", f"Got {r.status_code}", False)

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": "B" * 20001})
        report.ok("Over max length → 422") if r.status_code == 422 else report.fail("Over max length", f"Got {r.status_code}", True)

        sql_inject = "'; DROP TABLE postmortems; -- Database service failed for two hours. Root cause unknown. Action: investigate."
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": sql_inject})
        report.ok("SQL injection → safe") if r.status_code in [200, 422] else report.fail("SQL injection", f"Unexpected {r.status_code}", True)

        xss = "<script>alert('xss')</script> Database failure occurred affecting payment service for 2 hours. Root cause: connection pool."
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": xss})
        if r.status_code == 200:
            response_text = r.text
            if "<script>" not in response_text:
                report.ok("XSS sanitized", "Script tags not in response")
            else:
                report.fail("XSS sanitized", "Script tag found in response body", True)
        else:
            report.ok("XSS rejected", f"HTTP {r.status_code}")

        arabic = "فشل قاعدة البيانات مما أثر على خدمة الدفع لمدة ساعتين. السبب الجذري: استنفاد مجمع الاتصالات."
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": arabic})
        report.ok("Arabic text → 200") if r.status_code == 200 else report.warn("Arabic text", f"Got {r.status_code} — multilingual support")

        japanese = "データベース接続プールが枯渇し、支払いサービスが2時間停止しました。根本原因：接続数の上限設定が古いまま。"
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": japanese})
        report.ok("Japanese text → 200") if r.status_code == 200 else report.warn("Japanese text", f"Got {r.status_code}")

        emoji_text = "🔥🔥🔥 " * 20 + " service down fix deploy rollback incident production failure"
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": emoji_text})
        if r.status_code == 200:
            report.ok("Emoji-heavy text → 200")
        elif r.status_code == 429:
            report.ok("Emoji-heavy text → rate limited", "429 under chaos load — acceptable")
        else:
            report.warn("Emoji text", f"Got {r.status_code}")

    async def _test_boundaries(self, report):
        r = await self.client.post(
            f"{self.base_url}/api/v1/demo/analyze",
            content="not json",
            headers={"Content-Type": "text/plain"}
        )
        report.ok("Wrong content type → 422") if r.status_code == 422 else report.warn("Wrong content type", f"Got {r.status_code}")

        r = await self.post("/api/v1/demo/analyze", json={"raw_content": {"nested": "object"}})
        report.ok("Nested object → 422") if r.status_code == 422 else report.warn("Nested object", f"Got {r.status_code}")

        long_title_pm = "A" * 500 + " — database failure with connection pool issues for payment service."
        r = await self.post("/api/v1/demo/analyze", json={"raw_content": long_title_pm})
        report.ok("Long content line → handles gracefully") if r.status_code in [200, 422, 429] else report.fail("Long content line", f"Got {r.status_code}", False)

    async def _test_auth_security(self, report):
        r = await self.post("/api/v1/postmortems", json={"title": "Test", "incident_date": "2025-01-01", "raw_content": "test " * 15})
        report.ok("No auth → 401") if r.status_code == 401 else report.fail("Auth required", f"Got {r.status_code}, expected 401", True)

        r = await self.client.post(
            f"{self.base_url}/api/v1/postmortems",
            json={"title": "Test", "incident_date": "2025-01-01", "raw_content": "test " * 15},
            headers={"Authorization": "Bearer definitely.not.valid.jwt.token"}
        )
        report.ok("Bad JWT → 401") if r.status_code == 401 else report.warn("Bad JWT", f"Got {r.status_code}")

        r = await self.get("/health")
        response_text = r.text
        if "sk-ant-" in response_text or "ANTHROPIC" in response_text:
            report.fail("API key exposure", "Anthropic key visible in health response", True)
        else:
            report.ok("API key hidden", "No keys in health response")

    async def _test_concurrent(self, report):
        async def single_request():
            return await self.post("/api/v1/demo/analyze", json={
                "raw_content": "Database connection failure affecting payment service for 2 hours. No monitoring configured. Root cause: pool exhausted."
            })

        results = await asyncio.gather(*[single_request() for _ in range(8)], return_exceptions=True)
        successes = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code in [200, 429])
        errors = sum(1 for r in results if isinstance(r, Exception) or (hasattr(r, 'status_code') and r.status_code == 500))

        if errors == 0:
            report.ok("Concurrent load (8 req)", f"{successes}/8 succeeded or rate-limited, 0 errors")
        else:
            report.fail("Concurrent load", f"{errors} errors in 8 concurrent requests", True)

    async def _test_data_integrity(self, report):
        r1 = await self.get("/api/v1/demo/climax")
        r2 = await self.get("/api/v1/demo/climax")
        if r1.status_code == 200 and r2.status_code == 200:
            if r1.json().get("similarity_score") == r2.json().get("similarity_score"):
                report.ok("Climax endpoint deterministic", "Same score on repeat calls")
            else:
                report.warn("Climax endpoint", "Different scores on repeat calls — check caching")

        r1 = await self.get("/api/v1/demo/pattern-score")
        r2 = await self.get("/api/v1/demo/pattern-score")
        if r1.status_code == 200 and r2.status_code == 200:
            if r1.json().get("score") == r2.json().get("score"):
                report.ok("Pattern score deterministic", "Consistent on repeat calls")
            else:
                report.warn("Pattern score", "Different scores on repeat calls")

    async def _test_demo_stability(self, report):
        endpoints = [
            "/api/v1/demo/incidents",
            "/api/v1/demo/climax",
            "/api/v1/demo/pattern-score",
        ]
        all_ok = True
        for ep in endpoints:
            r = await self.get(ep)
            if r.status_code != 200:
                report.fail(f"Demo endpoint {ep}", f"HTTP {r.status_code}", True)
                all_ok = False
        if all_ok:
            report.ok("All demo endpoints stable", "200 on all demo routes")

        tasks = [self.get("/api/v1/demo/climax") for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception) or (hasattr(r, 'status_code') and r.status_code != 200)]
        if not errors:
            report.ok("Rapid demo calls", "5 rapid climax calls all returned 200")
        else:
            report.fail("Rapid demo calls", f"{len(errors)} errors under rapid access", True)

if __name__ == "__main__":
    agent = Day7ChaosAgent()
    asyncio.run(agent.execute("Full Chaos Agent", day=7))
