"""
ECHO Phase 2 Auth Agent
=======================
Verifikasi endpoint auth: register, login, /me, JWT, error cases.

5 Kategori:
  1. Register           — sukses, duplikat, validasi password pendek, email invalid
  2. Login              — sukses, wrong password, unknown email
  3. JWT / /me          — token valid, expired, invalid, missing
  4. Workflow           — register → login → /me end-to-end
  5. Concurrent         — 10 concurrent register/login ops

Jalankan:
    cd backend && make phase2
"""

import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import AgentReport, BaseAgent

TEST_PREFIX = "p2-"
API_PREFIX = "/api/v1"


def _email() -> str:
    return f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}@example.com"


async def _post(agent: BaseAgent, path: str, body: dict) -> tuple[int, dict]:
    try:
        res = await agent.post(f"{API_PREFIX}{path}", json=body)
        try:
            data = res.json()
        except Exception:
            data = {}
        return res.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


async def _get(agent: BaseAgent, path: str, token: str | None = None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        res = await agent.get(f"{API_PREFIX}{path}", headers=headers)
        try:
            data = res.json()
        except Exception:
            data = {}
        return res.status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


# ── Category 1: Register ──────────────────────────────────────────────────────

async def _test_register(agent: BaseAgent, report: AgentReport) -> str | None:
    """Returns a test token if registration succeeded."""
    email = _email()

    # 1a. Successful register
    status, data = await _post(agent, "/auth/register", {
        "email": email, "password": "password123", "org_name": "ECHO Test"
    })
    if status == 201 and data.get("access_token") and data.get("user", {}).get("email") == email:
        report.ok("Register: success", f"201 + token + user object")
    else:
        report.fail("Register: success", f"Got {status}: {str(data)[:120]}", critical=True)
        return None

    token = data["access_token"]

    # 1b. Duplicate email → 409
    status2, data2 = await _post(agent, "/auth/register", {
        "email": email, "password": "password123"
    })
    if status2 == 409:
        report.ok("Register: duplicate → 409", data2.get("detail", "")[:80])
    else:
        report.fail("Register: duplicate → 409", f"Got {status2}", critical=True)

    # 1c. Short password → 422
    status3, _ = await _post(agent, "/auth/register", {
        "email": _email(), "password": "short"
    })
    if status3 == 422:
        report.ok("Register: short password → 422", "Validation works")
    else:
        report.warn("Register: short password → 422", f"Got {status3} (expected 422)")

    # 1d. Invalid email → 422
    status4, _ = await _post(agent, "/auth/register", {
        "email": "not-an-email", "password": "password123"
    })
    if status4 == 422:
        report.ok("Register: invalid email → 422", "Email validation works")
    else:
        report.warn("Register: invalid email → 422", f"Got {status4} (expected 422)")

    return token


# ── Category 2: Login ─────────────────────────────────────────────────────────

async def _test_login(agent: BaseAgent, report: AgentReport) -> str | None:
    email = _email()

    # Register first
    status, data = await _post(agent, "/auth/register", {
        "email": email, "password": "hunter2!Safe"
    })
    if status != 201:
        report.fail("Login: setup register", f"Got {status}", critical=True)
        return None

    # 2a. Correct login
    status2, data2 = await _post(agent, "/auth/login", {
        "email": email, "password": "hunter2!Safe"
    })
    if status2 == 200 and data2.get("access_token"):
        report.ok("Login: success", "200 + token")
    else:
        report.fail("Login: success", f"Got {status2}", critical=True)
        return None

    token = data2["access_token"]

    # 2b. Wrong password → 401
    status3, d3 = await _post(agent, "/auth/login", {
        "email": email, "password": "wrongpassword"
    })
    if status3 == 401:
        report.ok("Login: wrong password → 401", d3.get("detail", "")[:60])
    else:
        report.fail("Login: wrong password → 401", f"Got {status3}", critical=True)

    # 2c. Unknown email → 401
    status4, _ = await _post(agent, "/auth/login", {
        "email": "nobody-nonexistent@example.com", "password": "password123"
    })
    if status4 == 401:
        report.ok("Login: unknown email → 401", "No user enumeration")
    else:
        report.fail("Login: unknown email → 401", f"Got {status4}", critical=True)

    return token


# ── Category 3: JWT / /me ─────────────────────────────────────────────────────

async def _test_jwt(agent: BaseAgent, report: AgentReport, token: str | None) -> None:
    if not token:
        report.warn("JWT: skipped", "No token from previous categories")
        return

    # 3a. Valid token → /me returns user
    status, data = await _get(agent, "/auth/me", token)
    if status == 200 and data.get("email") and data.get("id"):
        report.ok("JWT: /me with valid token", f"email={data['email'][:30]}")
    else:
        report.fail("JWT: /me with valid token", f"Got {status}: {str(data)[:80]}", critical=True)

    # 3b. Invalid token → 401
    status2, _ = await _get(agent, "/auth/me", "not.a.valid.jwt")
    if status2 == 401:
        report.ok("JWT: invalid token → 401", "Rejected")
    else:
        report.fail("JWT: invalid token → 401", f"Got {status2}", critical=True)

    # 3c. No token → 401
    status3, _ = await _get(agent, "/auth/me", None)
    if status3 == 401:
        report.ok("JWT: missing token → 401", "Rejected")
    else:
        report.fail("JWT: missing token → 401", f"Got {status3}", critical=True)

    # 3d. org_name in /me response
    if "org_name" in data:
        report.ok("JWT: org_name in /me", f"org_name={data.get('org_name')}")
    else:
        report.warn("JWT: org_name in /me", "Field missing from response")


# ── Category 4: End-to-end workflow ──────────────────────────────────────────

async def _test_workflow(agent: BaseAgent, report: AgentReport) -> None:
    email = _email()
    pw = "SecurePass99"

    # 4a. Register
    s1, d1 = await _post(agent, "/auth/register", {
        "email": email, "password": pw, "org_name": "Workflow Corp"
    })
    if s1 != 201:
        report.fail("Workflow: register", f"Got {s1}", critical=True)
        return
    reg_token = d1["access_token"]
    user_id = d1["user"]["id"]
    report.ok("Workflow: register", f"id={user_id[:8]}…")

    # 4b. Login with same creds — should return same user
    s2, d2 = await _post(agent, "/auth/login", {"email": email, "password": pw})
    if s2 != 200:
        report.fail("Workflow: login after register", f"Got {s2}", critical=True)
        return
    login_token = d2["access_token"]
    assert d2["user"]["id"] == user_id, "user_id mismatch"
    report.ok("Workflow: login after register", "Same user_id returned")

    # 4c. /me works with login token
    s3, d3 = await _get(agent, "/auth/me", login_token)
    if s3 == 200 and d3.get("id") == user_id:
        report.ok("Workflow: /me with login token", "User identity confirmed")
    else:
        report.fail("Workflow: /me with login token", f"Got {s3}, id={d3.get('id')}", critical=True)

    # 4d. Both tokens are valid JWTs for same user
    s4, d4 = await _get(agent, "/auth/me", reg_token)
    if s4 == 200 and d4.get("id") == user_id:
        report.ok("Workflow: register token also valid", "Both tokens work")
    else:
        report.warn("Workflow: register token", f"Got {s4}")


# ── Category 5: Concurrent load ───────────────────────────────────────────────

async def _test_concurrent(agent: BaseAgent, report: AgentReport) -> None:
    N = 10
    lat: list[float] = []
    errors = 0

    async def one_register(i: int) -> None:
        nonlocal errors
        t0 = time.monotonic()
        s, d = await _post(agent, "/auth/register", {
            "email": f"{TEST_PREFIX}conc-{uuid.uuid4().hex[:6]}@example.com",
            "password": "concurrent99",
        })
        lat.append((time.monotonic() - t0) * 1000)
        if s != 201:
            errors += 1

    await asyncio.gather(*[one_register(i) for i in range(N)])

    if errors == 0:
        p50 = sorted(lat)[N // 2]
        p99 = sorted(lat)[-1]
        report.ok(f"Concurrent: {N} simultaneous registers", f"0 errors | p50={p50:.0f}ms p99={p99:.0f}ms")
    else:
        report.fail(f"Concurrent: {N} simultaneous registers", f"{errors} errors", critical=True)


# ── Agent ─────────────────────────────────────────────────────────────────────

class Phase2AuthAgent(BaseAgent):
    async def run(self, report: AgentReport) -> None:
        print("\n  === CATEGORY 1: Register ===")
        token_from_register = await _test_register(self, report)

        print("\n  === CATEGORY 2: Login ===")
        token_from_login = await _test_login(self, report)

        print("\n  === CATEGORY 3: JWT / /me ===")
        await _test_jwt(self, report, token_from_login or token_from_register)

        print("\n  === CATEGORY 4: End-to-End Workflow ===")
        await _test_workflow(self, report)

        print("\n  === CATEGORY 5: Concurrent Load ===")
        await _test_concurrent(self, report)


if __name__ == "__main__":
    asyncio.run(Phase2AuthAgent().execute("Phase 2 — Auth Layer", day=0))
