from fastapi import APIRouter

from app.database import engine

router = APIRouter(tags=["health"])

TABEL_WAJIB = ["users", "postmortems"]


async def cek_koneksi_database() -> str:
    """Verifikasi PostgreSQL dapat dijangkau."""
    try:
        async with engine.connect() as koneksi:
            await koneksi.exec_driver_sql("SELECT 1")
        return "connected"
    except Exception:
        return "disconnected"


async def cek_pgvector() -> str:
    """Cek apakah extension pgvector aktif di PostgreSQL."""
    try:
        async with engine.connect() as koneksi:
            hasil = await koneksi.exec_driver_sql(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            baris = hasil.fetchone()
            return "enabled" if baris and baris[0] else "disabled"
    except Exception:
        return "disabled"


async def cek_tabel() -> dict[str, bool]:
    """Verifikasi setiap tabel wajib ada di schema public."""
    hasil: dict[str, bool] = {}
    try:
        async with engine.connect() as koneksi:
            for tabel in TABEL_WAJIB:
                baris = await koneksi.exec_driver_sql(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = $1)",
                    (tabel,),
                )
                hasil[tabel] = bool(baris.fetchone()[0])
    except Exception:
        for tabel in TABEL_WAJIB:
            hasil.setdefault(tabel, False)
    return hasil


@router.get("/health")
async def health_check():
    db_status = await cek_koneksi_database()
    connected = db_status == "connected"

    tabel_status = await cek_tabel() if connected else {t: False for t in TABEL_WAJIB}
    semua_tabel_ada = all(tabel_status.values())

    status = "ok" if connected and semua_tabel_ada else "degraded"

    return {
        "status": status,
        "database": db_status,
        "pgvector": await cek_pgvector() if connected else "unavailable",
        "tables": tabel_status,
    }
