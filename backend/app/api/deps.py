from __future__ import annotations

from fastapi import Depends

from app.core.container import get_rates_manager_service
from app.services.rates_manager_service import RatesManagerService
from app.realtime.connection_manager import ConnectionManager
from app.core.container import (
    get_connection_manager as _get_connection_manager_from_container,
)


def get_rates_manager(
    service: RatesManagerService = Depends(get_rates_manager_service),
) -> RatesManagerService:
    """
    Dependency wrapper used by FastAPI routes.

    This makes it easy to override the whole service in tests.
    """
    return service


def get_connection_manager() -> ConnectionManager:
    """
    Simple wrapper to retrieve the global ConnectionManager instance.

    Kept as a separate function so it can be overridden in tests if needed.
    """
    return _get_connection_manager_from_container()
