from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import settings

engine_options = {"echo": settings.APP_ENV != "production", "pool_pre_ping": True}
if ":6543/" in settings.DATABASE_URL:
    # Supabase transaction poolers do not support prepared statements or a
    # persistent client-side pool.
    engine_options.update(poolclass=NullPool, connect_args={"statement_cache_size": 0})

engine = create_async_engine(settings.DATABASE_URL, **engine_options)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db():
    from app.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session:
        yield session
