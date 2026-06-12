import pytest


@pytest.mark.asyncio
async def test_health(klien):
    respons = await klien.get("/health")
    assert respons.status_code == 200
    assert respons.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_demo_incidents(klien):
    respons = await klien.get("/api/v1/demo/incidents")
    assert respons.status_code == 200
    assert len(respons.json()) >= 8


@pytest.mark.asyncio
async def test_demo_climax(klien):
    respons = await klien.get("/api/v1/demo/climax")
    assert respons.status_code == 200
    data = respons.json()
    assert data["similarity_score"] > 0.8
    assert len(data["unimplemented_items"]) >= 2
