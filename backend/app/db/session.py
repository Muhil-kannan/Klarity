"""
Database session dependency for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.base import AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
