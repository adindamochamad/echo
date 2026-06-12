from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import wajib_auth
from app.limiter import limiter
from app.models import Postmortem
from app.schemas.demo import ActionItem, ActionItemStatus, AnalyzeResponse, RecurrenceMatch, Severity
from app.schemas.postmortem import PostmortemCreate, PostmortemOut
from app.services.analyze_service import analisis_lengkap
from app.services.claude_service import ekstrak_postmortem, normalisasi_hasil_ekstraksi
from app.services.embedding_service import build_embedding_text, embed_text
from app.services.search_service import days_between, search_similar

router = APIRouter(prefix="/postmortems", tags=["postmortems"])

UKURAN_MAX_BYTES = 5 * 1024 * 1024
PANJANG_MIN_KARAKTER = 50
TIPE_DIIZINKAN = {"text/plain", "text/markdown", "application/octet-stream"}
EKSTENSI_DIIZINKAN = {".txt", ".md"}


def _validasi_tipe_file(nama_file: str | None, content_type: str | None) -> None:
    if content_type == "application/pdf":
        raise HTTPException(status_code=415, detail="PDF not supported. Use .txt or .md")
    if content_type and content_type not in TIPE_DIIZINKAN:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {content_type}")
    if nama_file:
        ekstensi = "." + nama_file.rsplit(".", 1)[-1].lower() if "." in nama_file else ""
        if ekstensi and ekstensi not in EKSTENSI_DIIZINKAN:
            raise HTTPException(status_code=415, detail=f"Unsupported file extension: {ekstensi}")


def _pm_to_out(pm: Postmortem, recurrence_matches: list[RecurrenceMatch] | None = None) -> "PostmortemOut":
    return PostmortemOut(
        id=str(pm.id),
        title=pm.title,
        incident_date=pm.incident_date,
        severity=Severity(pm.severity) if pm.severity else None,
        summary=pm.summary or "",
        root_causes=pm.root_causes or [],
        action_items=[
            ActionItem(
                description=ai.get("description", ""),
                owner=ai.get("owner"),
                status=ActionItemStatus(ai.get("status", "OPEN")),
                ticket_ref=ai.get("ticket_ref"),
            )
            for ai in (pm.action_items or [])
        ],
        systems_affected=pm.systems_affected or [],
        has_recurrence=pm.has_recurrence,
        recurrence_matches=recurrence_matches or [],
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PostmortemOut)
async def buat_postmortem(
    body: PostmortemCreate,
    user_payload: dict = Depends(wajib_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a post-mortem: Claude extracts structure, Voyage AI generates embedding,
    saves to PostgreSQL, searches for recurrences via pgvector cosine similarity.
    """
    user_id = user_payload["sub"]

    # 1. Extract structure with Claude
    data_mentah = await ekstrak_postmortem(body.raw_content)
    data = normalisasi_hasil_ekstraksi(data_mentah)

    if body.severity:
        data["severity"] = body.severity

    # 2. Generate embedding — Voyage AI or hash fallback
    embed_input = build_embedding_text(
        body.raw_content, data["summary"], data["root_causes"], data["systems_affected"]
    )
    embedding = await embed_text(embed_input)

    # 3. Save to database
    pm = Postmortem(
        user_id=user_id,
        title=body.title,
        incident_date=str(body.incident_date),
        raw_content=body.raw_content,
        summary=data["summary"],
        root_causes=data["root_causes"],
        action_items=[ai.model_dump() for ai in data["action_items"]],
        severity=data["severity"].value if data["severity"] else None,
        systems_affected=data["systems_affected"],
        embedding=embedding,
        has_recurrence=False,
    )
    db.add(pm)
    await db.commit()
    await db.refresh(pm)

    # 4. Search for similar past incidents (exclude self)
    similar = await search_similar(db, embedding, user_id, exclude_id=str(pm.id))

    recurrence_matches = []
    for hit in similar:
        unimplemented = [
            ActionItem(
                description=ai.get("description", ""),
                owner=ai.get("owner"),
                status=ActionItemStatus(ai.get("status", "OPEN")),
                ticket_ref=ai.get("ticket_ref"),
            )
            for ai in (hit["action_items"] or [])
            if ai.get("status") in ("OPEN", "NEVER STARTED", "ABANDONED")
        ]
        recurrence_matches.append(RecurrenceMatch(
            incident_id=hit["id"],
            title=hit["title"],
            incident_date=hit["incident_date"],
            similarity_score=hit["similarity_score"],
            days_between=days_between(hit["incident_date"]),
            unimplemented_items=unimplemented,
        ))

    # 5. Mark has_recurrence if matches found
    if recurrence_matches:
        pm.has_recurrence = True
        await db.commit()

    return _pm_to_out(pm, recurrence_matches)


@router.get("", response_model=list[PostmortemOut])
async def daftar_postmortem(
    user_payload: dict = Depends(wajib_auth),
    db: AsyncSession = Depends(get_db),
):
    """List all postmortems for the authenticated user, newest first."""
    user_id = user_payload["sub"]
    rows = (await db.execute(
        select(Postmortem)
        .where(Postmortem.user_id == user_id)
        .order_by(desc(Postmortem.created_at))
    )).scalars().all()

    return [_pm_to_out(pm) for pm in rows]


@router.get("/{pm_id}", response_model=PostmortemOut)
async def ambil_postmortem(
    pm_id: str,
    user_payload: dict = Depends(wajib_auth),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single postmortem by ID (must belong to authenticated user)."""
    user_id = user_payload["sub"]
    pm = (await db.execute(
        select(Postmortem)
        .where(Postmortem.id == pm_id, Postmortem.user_id == user_id)
    )).scalar_one_or_none()

    if not pm:
        raise HTTPException(status_code=404, detail="Postmortem not found")

    return _pm_to_out(pm)


@router.post("/demo-import", response_model=AnalyzeResponse)
@limiter.limit(settings.DEMO_RATE_LIMIT)
async def impor_demo(request: Request, file: Annotated[UploadFile, File()]):
    """Import file post-mortem for demo (no auth, rate-limited)."""
    _validasi_tipe_file(file.filename, file.content_type)

    konten = await file.read()
    if len(konten) > UKURAN_MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Max 5MB.")

    teks = konten.decode("utf-8", errors="replace").strip()
    if len(teks) < PANJANG_MIN_KARAKTER:
        raise HTTPException(status_code=422, detail="File content too short")

    return await analisis_lengkap(teks)
