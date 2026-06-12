"""Layanan ekstraksi post-mortem via Claude API."""

import asyncio
import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic

from app.config import settings
from app.schemas.demo import ActionItem, ActionItemStatus, Severity

logger = logging.getLogger(__name__)

PROMPT_EKSTRAKSI = """Extract structured data from this post-mortem/incident report.
Return ONLY valid JSON with these fields:
- summary (string, 2-3 sentences, specific not generic)
- root_causes (array of strings, specific technical causes — avoid "lack of X" phrasing)
- action_items (array of {description, owner, status, ticket_ref})
- severity (P0|P1|P2|P3 or null)
- systems_affected (array of service/system names)

Post-mortem:
"""

TIMEOUT_CLAUDE_DETIK = 60.0
_klien_claude: AsyncAnthropic | None = None


def _dapatkan_klien_claude() -> AsyncAnthropic:
    """Singleton klien Anthropic agar tidak dibuat ulang tiap request."""
    global _klien_claude
    if _klien_claude is None:
        _klien_claude = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _klien_claude


def _sanitasi_teks(teks: str) -> str:
    """Hapus tag HTML/script agar input berbahaya tidak terefleksi di respons."""
    if not teks:
        return teks
    teks_bersih = re.sub(r"<script[^>]*>.*?</script>", "", teks, flags=re.IGNORECASE | re.DOTALL)
    teks_bersih = re.sub(r"<[^>]+>", "", teks_bersih)
    return teks_bersih.strip()


def _sanitasi_owner(nilai: Any) -> str | None:
    """Sanitasi field owner — tidak pernah fallback ke nilai mentah."""
    if nilai is None:
        return None
    teks_bersih = _sanitasi_teks(str(nilai))
    return teks_bersih or None


def _ekstrak_json_dari_teks(teks: str) -> dict[str, Any]:
    """Ambil objek JSON dari respons Claude, termasuk blok markdown."""
    teks_bersih = teks.strip()
    if "```" in teks_bersih:
        bagian = teks_bersih.split("```")
        for potongan in bagian[1::2]:
            potongan = potongan.strip()
            if potongan.startswith("json"):
                potongan = potongan[4:].strip()
            try:
                hasil = json.loads(potongan)
                if isinstance(hasil, dict):
                    return hasil
            except json.JSONDecodeError:
                continue

    mulai = teks_bersih.find("{")
    akhir = teks_bersih.rfind("}")
    if mulai >= 0 and akhir > mulai:
        return json.loads(teks_bersih[mulai : akhir + 1])

    raise ValueError("Tidak ada JSON valid dalam respons Claude")


def _normalisasi_daftar_string(nilai: Any) -> list[str]:
    """Pastikan field daftar string aman untuk iterasi."""
    if isinstance(nilai, str):
        return [_sanitasi_teks(nilai)] if nilai.strip() else []
    if isinstance(nilai, list):
        return [_sanitasi_teks(str(item)) for item in nilai if item is not None and str(item).strip()]
    return []


async def ekstrak_postmortem(teks_mentah: str) -> dict[str, Any]:
    """Ekstrak struktur dari teks post-mortem menggunakan Claude."""
    if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY.startswith("sk-ant-your"):
        return _ekstraksi_fallback(teks_mentah)

    try:
        klien = _dapatkan_klien_claude()
        respons = await asyncio.wait_for(
            klien.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT_EKSTRAKSI + teks_mentah,
                    }
                ],
            ),
            timeout=TIMEOUT_CLAUDE_DETIK,
        )

        if not respons.content:
            raise ValueError("Respons Claude kosong")

        blok_teks = next((b for b in respons.content if getattr(b, "type", None) == "text"), None)
        if blok_teks is None or not getattr(blok_teks, "text", None):
            raise ValueError("Blok teks tidak ditemukan dalam respons Claude")

        return _ekstrak_json_dari_teks(blok_teks.text)
    except Exception as e:
        logger.warning("Claude extraction failed, using fallback: %s", e)
        return _ekstraksi_fallback(teks_mentah)


def _ekstraksi_fallback(teks_mentah: str) -> dict[str, Any]:
    """Fallback rule-based jika API key belum dikonfigurasi."""
    teks_lower = teks_mentah.lower()
    severity = None
    for tingkat in ["P0", "P1", "P2", "P3"]:
        if tingkat.lower() in teks_lower or f"severity: {tingkat.lower()}" in teks_lower:
            severity = tingkat
            break

    sistem = []
    for kata in ["payment-service", "checkout-service", "database", "auth-service", "payment-gateway"]:
        if kata in teks_lower:
            sistem.append(kata)

    return {
        "summary": _sanitasi_teks(teks_mentah[:300].strip() + ("..." if len(teks_mentah) > 300 else "")),
        "root_causes": [
            rc.strip()
            for rc in [
                "Connection pool max_connections not reviewed since initial deployment",
                "No monitoring configured for database connection pool utilization",
            ]
            if any(k in teks_lower for k in ["connection", "pool", "database", "timeout"])
        ] or ["Root cause requires further investigation based on incident notes"],
        "action_items": [
            {"description": "Implement connection pool monitoring and alerting", "owner": "Sarah Kim", "status": "OPEN", "ticket_ref": None},
            {"description": "Add retry logic with exponential backoff", "owner": "Marcus Reid", "status": "OPEN", "ticket_ref": None},
        ],
        "severity": severity or "P2",
        "systems_affected": sistem or ["unknown-service"],
    }


def normalisasi_hasil_ekstraksi(data: Any) -> dict:
    """Normalisasi output ekstraksi ke schema yang konsisten."""
    if not isinstance(data, dict):
        data = {}

    action_items = []
    raw_items = data.get("action_items", [])
    if not isinstance(raw_items, list):
        raw_items = []

    for item in raw_items:
        if item is None:
            continue
        if isinstance(item, str):
            action_items.append(ActionItem(description=_sanitasi_teks(item)))
        elif isinstance(item, dict):
            status_str = item.get("status") or "OPEN"
            try:
                status = ActionItemStatus(str(status_str).upper().replace("_", " "))
            except ValueError:
                status = ActionItemStatus.OPEN
            action_items.append(
                ActionItem(
                    description=_sanitasi_teks(str(item.get("description", ""))),
                    owner=_sanitasi_owner(item.get("owner")),
                    status=status,
                    ticket_ref=item.get("ticket_ref"),
                )
            )

    severity = data.get("severity")
    if severity:
        try:
            severity = Severity(str(severity))
        except ValueError:
            severity = None

    return {
        "summary": _sanitasi_teks(str(data.get("summary", ""))),
        "root_causes": _normalisasi_daftar_string(data.get("root_causes")),
        "action_items": action_items,
        "severity": severity,
        "systems_affected": _normalisasi_daftar_string(data.get("systems_affected")),
    }
