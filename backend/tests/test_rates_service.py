from datetime import datetime
from typing import Iterable, List

import pytest

from app.services.rates_manager_service import (
    InternalTick,
    RatesManagerService,
    PairPublicState,
)


def ts(value: str) -> datetime:
    # Helper to create a timezone-aware timestamp from an ISO string
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class DummyHourlyAvgRepo:
    """
    Minimal fake repository used only for unit tests.

    It implements the two methods that RatesManagerService expects:
    - get_latest_for_pairs
    - save

    For these tests we do not care about persistence, only that calls succeed.
    """

    async def get_latest_for_pairs(self, pairs: Iterable[str]) -> List[object]:
        # No initial averages for tests
        return []

    async def save(
        self, pair: str, hour_start: datetime, avg_price: float, count: int
    ) -> None:
        # In these tests we do not assert on persistence,
        # so this is intentionally a no-op.
        return None


def make_service() -> RatesManagerService:
    # Helper to create a service with a dummy repository
    repo = DummyHourlyAvgRepo()
    return RatesManagerService(hourly_avg_repo=repo)


@pytest.mark.asyncio
async def test_ingest_tick_updates_price() -> None:
    # A single tick should update the pair state with the latest price
    svc = make_service()

    tick = InternalTick(
        pair="ETH/USDC",
        price=2000.0,
        timestamp=ts("2025-01-01T10:00:00Z"),
    )

    await svc.ingest_tick(tick)

    state: PairPublicState | None = svc.get_pair_state("ETH/USDC")
    assert state is not None
    assert state.price == 2000.0
    # We do not assert the exact timestamp value, just that it was set
    assert state.last_update is not None


@pytest.mark.asyncio
async def test_hourly_average_uses_multiple_ticks_in_same_hour() -> None:
    # When multiple ticks arrive in the same hour, the hourly average
    # should be the arithmetic mean of all prices in that bucket.
    svc = make_service()

    await svc.ingest_tick(
        InternalTick(
            pair="ETH/USDC",
            price=2000.0,
            timestamp=ts("2025-01-01T10:05:00Z"),
        )
    )
    await svc.ingest_tick(
        InternalTick(
            pair="ETH/USDC",
            price=2100.0,
            timestamp=ts("2025-01-01T10:15:00Z"),
        )
    )

    state = svc.get_pair_state("ETH/USDC")
    assert state is not None
    # Expected average: (2000 + 2100) / 2 = 2050
    assert state.hourly_avg is not None
    assert abs(state.hourly_avg - 2050.0) < 1e-6


@pytest.mark.asyncio
async def test_ticks_for_different_pairs_do_not_mix() -> None:
    # Each pair should maintain its own independent state
    svc = make_service()

    await svc.ingest_tick(
        InternalTick(
            pair="ETH/USDC",
            price=2000.0,
            timestamp=ts("2025-01-01T10:00:00Z"),
        )
    )
    await svc.ingest_tick(
        InternalTick(
            pair="ETH/USDT",
            price=3000.0,
            timestamp=ts("2025-01-01T10:00:00Z"),
        )
    )

    usdc = svc.get_pair_state("ETH/USDC")
    usdt = svc.get_pair_state("ETH/USDT")

    assert usdc is not None
    assert usdt is not None

    assert usdc.price == 2000.0
    assert usdt.price == 3000.0
