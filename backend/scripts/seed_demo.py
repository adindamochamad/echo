"""Script seed demo — idempotent, aman dijalankan berulang."""

import asyncio
import logging
import sys
from pathlib import Path

# Agar bisa dijalankan langsung: python scripts/seed_demo.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)


async def seed():
    """Aktifkan pgvector dan buat tabel dasar jika belum ada."""
    async with engine.begin() as koneksi:
        await koneksi.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await koneksi.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await koneksi.execute(
            text("""
            CREATE TABLE IF NOT EXISTS postmortems (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title TEXT NOT NULL,
                incident_date DATE NOT NULL,
                raw_content TEXT NOT NULL,
                summary TEXT,
                severity TEXT,
                systems_affected TEXT[],
                root_causes JSONB DEFAULT '[]',
                action_items JSONB DEFAULT '[]',
                embedding vector(1536),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """)
        )
    logger.info("Seed selesai — pgvector aktif, tabel postmortems siap")
    logger.info("Demo data dilayani via app/services/demo_data.py (8 insiden)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
