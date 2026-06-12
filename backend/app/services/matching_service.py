"""Engine pencocokan kemiripan insiden — keyword, sistem, dan frasa domain."""

import re
from difflib import SequenceMatcher

from app.schemas.demo import RecurrenceMatch
from app.services.demo_data import (
    CLIMAX_CURRENT_ID,
    DEMO_INCIDENTS,
    hitung_hari_antar_insiden,
    tanggal_insiden_sekarang_demo,
)

# Kata kunci domain insiden infrastruktur
KATA_KUNCI_DOMAIN = {
    "connection", "pool", "database", "timeout", "checkout", "payment",
    "monitoring", "cascade", "retry", "load", "utilization", "failover",
    "backoff", "alerting", "saturation", "limits",
}

# Frasa multi-kata yang menandakan pola recurrence yang sama
FRASA_DOMAIN = [
    "connection pool",
    "connection timeout",
    "pool utilization",
    "load test",
    "load testing",
    "connection limits",
    "pool monitoring",
    "retry logic",
    "pool exhausted",
    "timeout cascade",
    "max_connections",
    "pool limits reached",
    "pool limits",
    "not increased since",
    "never reviewed since",
]

STATUS_BELUM_DIKERJAKAN = ("NEVER STARTED", "ABANDONED", "OPEN")


def bangun_teks_untuk_matching(teks_mentah: str, data: dict) -> str:
    """Gabungkan teks mentah dan hasil ekstraksi untuk matching yang lebih akurat."""
    bagian = [teks_mentah, data.get("summary", "")]
    bagian.extend(data.get("root_causes", []))
    bagian.extend(data.get("systems_affected", []))
    return " ".join(str(b) for b in bagian if b)


def _tokenize(teks: str) -> set[str]:
    """Tokenisasi teks untuk perbandingan keyword."""
    return set(re.findall(r"[a-z0-9-]+", teks.lower()))


def _bangun_korpus_insiden(insiden) -> str:
    """Gabungkan semua field insiden untuk perbandingan kaya konteks."""
    deskripsi_tindakan = " ".join(ai.description for ai in insiden.action_items)
    return " ".join(
        [
            insiden.title,
            insiden.summary,
            " ".join(insiden.root_causes),
            " ".join(insiden.systems_affected),
            deskripsi_tindakan,
        ]
    )


def _skor_frasa_domain(teks_baru: str, korpus_lama: str) -> float:
    """Skor berdasarkan frasa domain yang muncul di kedua teks."""
    teks_baru_lower = teks_baru.lower()
    korpus_lama_lower = korpus_lama.lower()
    jumlah_cocok = sum(
        1 for frasa in FRASA_DOMAIN
        if frasa in teks_baru_lower and frasa in korpus_lama_lower
    )
    return min(0.25, jumlah_cocok * 0.08)


def _skor_sistem(teks_baru: str, insiden) -> float:
    """Boost jika sistem yang disebut overlap — pakai word boundary agar tidak false positive."""
    teks_lower = teks_baru.lower()
    sistem_cocok = [
        s for s in insiden.systems_affected
        if re.search(rf"\b{re.escape(s.lower())}\b", teks_lower)
    ]
    if not insiden.systems_affected:
        return 0.0
    return 0.15 * (len(sistem_cocok) / len(insiden.systems_affected))


def hitung_skor_kemiripan(teks_baru: str, insiden_lama) -> float:
    """Hitung skor kemiripan 0-1 antara teks baru dan insiden historis."""
    korpus_lama = _bangun_korpus_insiden(insiden_lama)
    token_baru = _tokenize(teks_baru)
    token_lama = _tokenize(korpus_lama)

    if not token_baru or not token_lama:
        return 0.0

    irisan = len(token_baru & token_lama)
    gabungan = len(token_baru | token_lama)
    jaccard = irisan / gabungan if gabungan else 0.0

    sequence = SequenceMatcher(None, teks_baru.lower(), korpus_lama.lower()).ratio()

    overlap_domain = KATA_KUNCI_DOMAIN & token_baru & token_lama
    kata_domain_baru = KATA_KUNCI_DOMAIN & token_baru
    skor_domain = (
        len(overlap_domain) / len(kata_domain_baru) * 0.30
        if kata_domain_baru
        else 0.0
    )

    skor_frasa = _skor_frasa_domain(teks_baru, korpus_lama)
    skor_sistem = _skor_sistem(teks_baru, insiden_lama)

    return min(
        1.0,
        jaccard * 0.30 + sequence * 0.20 + skor_domain + skor_frasa + skor_sistem,
    )


def _hitung_hari_sejak_match(tanggal_insiden_lama: str) -> int:
    """Selisih hari dari insiden historis ke insiden 'hari ini' dalam narasi demo."""
    return hitung_hari_antar_insiden(tanggal_insiden_lama, tanggal_insiden_sekarang_demo())


def cari_recurrence(teks_baru: str, ambang: float = 0.45) -> list[RecurrenceMatch]:
    """Cari insiden historis yang mirip dengan teks baru."""
    hasil: list[RecurrenceMatch] = []

    for insiden in DEMO_INCIDENTS:
        # Jangan match insiden 'hari ini' — itu bukan recurrence historis
        if insiden.id == CLIMAX_CURRENT_ID:
            continue

        skor = hitung_skor_kemiripan(teks_baru, insiden)
        if skor >= ambang:
            belum_dikerjakan = [
                ai
                for ai in insiden.action_items
                if ai.status.value in STATUS_BELUM_DIKERJAKAN
            ]
            hasil.append(
                RecurrenceMatch(
                    incident_id=insiden.id,
                    title=insiden.title,
                    incident_date=insiden.incident_date,
                    similarity_score=round(skor, 2),
                    days_between=_hitung_hari_sejak_match(insiden.incident_date),
                    unimplemented_items=belum_dikerjakan,
                )
            )

    hasil.sort(key=lambda x: x.similarity_score, reverse=True)
    return hasil

