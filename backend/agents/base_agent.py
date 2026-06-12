import httpx
import asyncio
import sys
import json
from datetime import datetime
from typing import Callable

# ANSI colors for terminal output
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

class AgentReport:
    def __init__(self, agent_name: str, day: int):
        self.agent_name = agent_name
        self.day = day
        self.passed = []
        self.failed = []
        self.warnings = []
        self.start_time = datetime.now()

    def ok(self, test_name: str, detail: str = ""):
        self.passed.append((test_name, detail))
        print(f"  {GREEN}✓{RESET} {test_name}" + (f" — {detail}" if detail else ""))

    def fail(self, test_name: str, detail: str = "", critical: bool = True):
        self.failed.append((test_name, detail, critical))
        level = f"{RED}✗ FAIL{RESET}" if critical else f"{YELLOW}⚠ WARN{RESET}"
        print(f"  {level} {test_name}" + (f" — {detail}" if detail else ""))
        if not critical:
            self.warnings.append((test_name, detail))

    def warn(self, test_name: str, detail: str = ""):
        self.fail(test_name, detail, critical=False)

    def print_summary(self) -> int:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        critical_fails = [f for f in self.failed if f[2]]
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}ECHO Agent — Day {self.day}: {self.agent_name}{RESET}")
        print(f"{'='*60}")
        print(f"  {GREEN}Passed:{RESET}   {len(self.passed)}")
        print(f"  {YELLOW}Warnings:{RESET} {len(self.warnings)}")
        print(f"  {RED}Failed:{RESET}   {len(critical_fails)}")
        print(f"  Time:     {elapsed:.1f}s")
        print(f"{'='*60}")

        if critical_fails:
            print(f"\n{RED}{BOLD}CRITICAL FAILURES — DO NOT PROCEED:{RESET}")
            for name, detail, _ in critical_fails:
                print(f"  → {name}: {detail}")
            print(f"\n{RED}Fix all critical failures before Day {self.day + 1}.{RESET}\n")
            return 2
        elif self.warnings:
            print(f"\n{YELLOW}Warnings detected — review before proceeding.{RESET}\n")
            return 1
        else:
            print(f"\n{GREEN}{BOLD}All checks passed. Safe to proceed to Day {self.day + 1}.{RESET}\n")
            return 0

class BaseAgent:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.client.get(f"{self.base_url}{path}", **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.client.post(f"{self.base_url}{path}", **kwargs)

    async def run(self, report: AgentReport):
        raise NotImplementedError

    async def execute(self, agent_name: str, day: int):
        report = AgentReport(agent_name, day)
        print(f"\n{BLUE}{BOLD}Running ECHO Agent — Day {day}: {agent_name}{RESET}")
        print(f"{BLUE}Target: {self.base_url}{RESET}\n")
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client
            await self.run(report)
        exit_code = report.print_summary()
        sys.exit(exit_code)
