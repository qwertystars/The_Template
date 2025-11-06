"""
Database configuration and session management.
Uses async SQLAlchemy with connection pooling.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, MetaData

from app.core.config import settings


# Naming convention for database constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


# Create async engine with connection pooling
if settings.TESTING:
    # Use NullPool for testing to avoid connection issues
    engine = create_async_engine(
        str(settings.TEST_DATABASE_URL or settings.DATABASE_URL),
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_POOL_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Enable connection health checks
        poolclass=QueuePool,
    )


# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create all tables.
    Use Alembic migrations in production instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


# Database event listeners for logging and debugging
if settings.DEBUG:
    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log database connections."""
        print(f"New DB connection: {id(dbapi_conn)}")

    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout from pool."""
        print(f"Connection checked out: {id(dbapi_conn)}")


# Query helpers for common patterns
class DatabaseManager:
    """Helper class for common database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit_or_rollback(self) -> None:
        """Commit transaction or rollback on error."""
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def flush(self) -> None:
        """Flush pending changes without committing."""
        await self.session.flush()

    async def refresh(self, instance: Base) -> None:
        """Refresh instance from database."""
        await self.session.refresh(instance)

    async def delete(self, instance: Base) -> None:
        """Delete instance."""
        await self.session.delete(instance)
        await self.commit_or_rollback()

    async def bulk_insert(self, instances: list[Base]) -> None:
        """Bulk insert instances."""
        self.session.add_all(instances)
        await self.commit_or_rollback()
