from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.limiter import limiter
from app.schemas.demo import (
    AnalyzeRequest,
    AnalyzeResponse,
    ActionItemStatus,
    ClimaxResponse,
    PatternScoreResponse,
)
from app.services.analyze_service import analisis_lengkap
from app.services.demo_data import (
    CLIMAX_CURRENT_ID,
    CLIMAX_MATCHED_ID,
    DEMO_INCIDENTS,
    buat_echo_verdict,
    hitung_hari_antar_insiden,
    hitung_pattern_score,
)
from app.services.matching_service import STATUS_BELUM_DIKERJAKAN, hitung_skor_kemiripan

router = APIRouter(prefix="/demo", tags=["demo"])


def _cari_insiden_demo(id_insiden: str):
    for insiden in DEMO_INCIDENTS:
        if insiden.id == id_insiden:
            return insiden
    raise HTTPException(status_code=503, detail="Demo climax data unavailable")


def _bangun_teks_insiden(insiden) -> str:
    """Build a flat text representation of an incident for similarity scoring."""
    return " ".join(
        [insiden.title, insiden.summary]
        + insiden.root_causes
        + insiden.systems_affected
    )


@router.get("/incidents")
async def daftar_insiden_demo():
    return DEMO_INCIDENTS


@router.get("/climax", response_model=ClimaxResponse)
async def demo_climax():
    insiden_sekarang = _cari_insiden_demo(CLIMAX_CURRENT_ID)
    insiden_lama = _cari_insiden_demo(CLIMAX_MATCHED_ID)
    belum_dikerjakan = [
        ai
        for ai in insiden_lama.action_items
        if ai.status.value in STATUS_BELUM_DIKERJAKAN
    ]

    teks_current = _bangun_teks_insiden(insiden_sekarang)
    similarity_score = round(hitung_skor_kemiripan(teks_current, insiden_lama), 2)

    return ClimaxResponse(
        title=insiden_sekarang.title,
        incident_date=insiden_sekarang.incident_date,
        severity=insiden_sekarang.severity,
        summary=insiden_sekarang.summary,
        systems_affected=insiden_sekarang.systems_affected,
        similarity_score=similarity_score,
        days_between=hitung_hari_antar_insiden(
            insiden_lama.incident_date, insiden_sekarang.incident_date
        ),
        matched_incident_title=insiden_lama.title,
        matched_incident_date=insiden_lama.incident_date,
        unimplemented_items=belum_dikerjakan[:3],
        echo_verdict=buat_echo_verdict(insiden_lama),
    )


@router.get("/pattern-score", response_model=PatternScoreResponse)
async def demo_pattern_score():
    stats = hitung_pattern_score(DEMO_INCIDENTS)
    return PatternScoreResponse(**stats)


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(settings.DEMO_RATE_LIMIT)
async def demo_analyze(request: Request, body: AnalyzeRequest):
    return await analisis_lengkap(body.raw_content, severity_hint=body.severity_hint)
