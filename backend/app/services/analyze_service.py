"""Alur analisis lengkap: ekstraksi Claude + pencocokan recurrence."""

from app.schemas.demo import AnalyzeResponse, Severity
from app.services.claude_service import ekstrak_postmortem, normalisasi_hasil_ekstraksi
from app.services.matching_service import bangun_teks_untuk_matching, cari_recurrence


async def analisis_lengkap(
    teks_mentah: str,
    severity_hint: Severity | None = None,
) -> AnalyzeResponse:
    """Ekstrak post-mortem dan cari pola recurrence dari konteks gabungan."""
    data_mentah = await ekstrak_postmortem(teks_mentah)
    data = normalisasi_hasil_ekstraksi(data_mentah)

    if severity_hint is not None:
        data["severity"] = severity_hint

    teks_matching = bangun_teks_untuk_matching(teks_mentah, data)
    matches = cari_recurrence(teks_matching)

    return AnalyzeResponse(
        summary=data["summary"],
        root_causes=data["root_causes"],
        action_items=data["action_items"],
        severity=data["severity"],
        systems_affected=data["systems_affected"],
        recurrence_matches=matches,
    )
