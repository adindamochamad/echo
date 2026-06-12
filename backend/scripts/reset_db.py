"""
Reset database Phase 1.

Menghapus semua tabel dan membuat ulang dari models.py + menambahkan
ivfflat index yang tidak bisa dikodekan lewat SQLAlchemy metadata.

Jalankan SEKALI saat schema berubah atau DB kotor:
    cd backend
    python scripts/reset_db.py

PERINGATAN: Semua data akan dihapus.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

# Import models agar terdaftar di Base.metadata sebelum create_all
import app.models  # noqa: F401
from app.database import Base


async def reset() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Extensions — idempotent
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        print("✓ Extensions: pgcrypto, vector")

        # Drop semua tabel (CASCADE menangani FK)
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ Tables dropped")

        # Buat ulang dari ORM models
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created from models.py")

        # ivfflat index tidak bisa dikodekan di ORM metadata — tambahkan manual
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_postmortems_embedding_cosine "
                "ON postmortems USING ivfflat (embedding vector_cosine_ops) "
                "WITH (lists = 10)"
            )
        )
        print("✓ ivfflat index created")

        # Index composite untuk listing per user
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_postmortems_user_created "
                "ON postmortems (user_id, created_at DESC)"
            )
        )
        print("✓ Composite index (user_id, created_at) created")

    await engine.dispose()
    print("\nDatabase reset selesai. Jalankan 'make phase1' untuk verifikasi.")


if __name__ == "__main__":
    asyncio.run(reset())
