from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base # Импортируем declarative_base здесь

from database.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

# Используйте этот Base в ваших файлах моделей (models.py)
Base = declarative_base()

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)

# Переименовал для ясности и экспорта
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False # Обычно полезно добавить
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get an async session."""
    async with AsyncSessionLocal() as session:
        yield session
