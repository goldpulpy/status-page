"""DI containers."""

from pathlib import Path

from dependency_injector import containers, providers
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.slowapi import rate_limit_func
from app.monitoring.manager import WorkerManager
from app.monitoring.scheduler import WorkerScheduler
from app.repositories.uow import SqlAlchemyUnitOfWork
from app.services.health.db import DatabaseHealthCheckService
from app.shared import config


class DatabaseContainer(containers.DeclarativeContainer):
    """Database container."""

    engine = providers.Singleton(
        create_async_engine,
        config.db.url,
        future=True,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


class Container(containers.DeclarativeContainer):
    """DI container."""

    db = providers.Container(DatabaseContainer)

    uow_factory = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=db.session_factory,
    )

    database_health = providers.Factory(
        DatabaseHealthCheckService,
        session_factory=db.session_factory,
    )

    jinja = providers.Singleton(
        Jinja2Templates,
        directory=Path(__file__).parent / "frontend" / "templates",
    )

    limiter = providers.Singleton(
        Limiter,
        key_func=rate_limit_func,
    )

    worker_manager = providers.Singleton(WorkerManager)

    worker_scheduler = providers.Singleton(
        WorkerScheduler,
        manager=worker_manager,
        uow_factory=uow_factory.provider,
    )
