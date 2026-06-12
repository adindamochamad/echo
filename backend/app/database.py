from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def dapatkan_sesi_db():
    """Dependency untuk mendapatkan sesi database async."""
    async with SessionLocal() as sesi:
        yield sesi


# Alias English name for use in routers
get_db = dapatkan_sesi_db
