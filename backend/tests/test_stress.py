"""Stress tests — jalankan dengan: make test-stress"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

KONTEN_UJI = (
    "Database connection pool exhausted during peak traffic. "
    "Payment service down for 3 hours. No monitoring configured. "
    "Root cause: max_connections=20 not reviewed. Action: increase limits, add alerting."
)


@pytest.mark.asyncio
async def test_concurrent_analyze():
    """8 request bersamaan tidak boleh menghasilkan 500."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as klien:

        async def satu_request():
            return await klien.post("/api/v1/demo/analyze", json={"raw_content": KONTEN_UJI})

        hasil = await asyncio.gather(*[satu_request() for _ in range(8)])
        error_500 = [r for r in hasil if r.status_code == 500]
        assert len(error_500) == 0
