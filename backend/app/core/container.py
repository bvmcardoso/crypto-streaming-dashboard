from __future__ import annotations

from functools import lru_cache

from app.core.database import AsyncSessionFactory
from app.repositories.hourly_average_repo import SqlAlchemyHourlyAverageRepository
from app.services.rates_manager_service import RatesManagerService
from app.realtime.connection_manager import ConnectionManager


@lru_cache
def get_hourly_average_repo() -> SqlAlchemyHourlyAverageRepository:
    """Return the concrete implementation for the hourly averages repository."""
    return SqlAlchemyHourlyAverageRepository(session_factory=AsyncSessionFactory)


@lru_cache
def get_rates_manager_service() -> RatesManagerService:
    """
    Return the singleton RatesManagerService instance.

    Using lru_cache here ensures we only create one service instance
    for the lifetime of the application process.
    """
    repo = get_hourly_average_repo()
    return RatesManagerService(hourly_avg_repo=repo)


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """
    Return a singleton ConnectionManager instance used by WebSocket routes
    and background tasks.
    """
    return ConnectionManager()
