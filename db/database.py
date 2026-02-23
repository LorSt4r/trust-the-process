import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()

# Build connection string for aiosqlite (local testing)
# We use a local file 'value_betting.db'
if os.getenv("USE_SQLITE", "true").lower() == "true":
    DATABASE_URL = "sqlite+aiosqlite:///value_betting.db"
else:
    DB_USER = os.getenv("POSTGRES_USER", "value_user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "value_password")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "value_betting")
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if os.getenv("USE_SQLITE", "true").lower() == "true":
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10
    )

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def init_db():
    from db.models import Base
    async with engine.begin() as conn:
        # Create all tables (useful for dev if Alembic is not used immediately)
        await conn.run_sync(Base.metadata.create_all)
