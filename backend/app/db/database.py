"""SQLAlchemy async engine and session factory."""

from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# SQLite doesn't support pool_pre_ping
_is_sqlite = settings.database_url.startswith("sqlite")
engine_kwargs: dict = {
    "echo": False,
}
if not _is_sqlite:
    engine_kwargs["pool_pre_ping"] = True
else:
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "timeout": 60.0,
    }

engine = create_async_engine(settings.database_url, **engine_kwargs)


from sqlalchemy import event  # noqa: E402


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if _is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()


async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables."""
    # Import models so they register with Base.metadata
    from app.db.models import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
