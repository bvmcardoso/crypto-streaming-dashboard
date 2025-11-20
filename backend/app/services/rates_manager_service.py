from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, Iterable, List, Optional

from app.repositories.protocol import HourlyAverageRepository
from app.schemas.rates import RateUpdateMessage


SUPPORTED_PAIRS: tuple[str, ...] = ("ETH/USDC", "ETH/USDT", "ETH/BTC")


@dataclass
class InternalTick:
    """Domain-level representation of a price tick coming from Finnhub."""

    pair: str
    price: float
    timestamp: datetime


@dataclass
class PairRuntimeState:
    """In-memory aggregation state for a single trading pair."""

    pair: str
    last_price: Optional[float] = None
    last_update: Optional[datetime] = None

    # Current hour aggregation:
    hour_start: Optional[datetime] = None
    sum_prices: float = 0.0
    count: int = 0
    hourly_avg: Optional[float] = None


@dataclass
class PairPublicState:
    """Public-facing state used by higher layers (REST, WebSocket)."""

    pair: str
    price: Optional[float]
    hourly_avg: Optional[float]
    last_update: Optional[datetime]


class RatesManagerService:
    """
    Core domain service responsible for:

    - Maintaining in-memory state of the latest price per pair
    - Aggregating ticks into hourly averages
    - Persisting hourly averages via the repository when an hour is closed
    - Optionally notifying an external listener (e.g. WebSocket manager)
      whenever a new tick is processed
    """

    def __init__(
        self,
        hourly_avg_repo: HourlyAverageRepository,
        supported_pairs: Iterable[str] | None = None,
    ) -> None:
        self._repo = hourly_avg_repo
        self._pairs: tuple[str, ...] = tuple(supported_pairs or SUPPORTED_PAIRS)

        # In-memory state keyed by pair symbol
        self._state: Dict[str, PairRuntimeState] = {
            pair: PairRuntimeState(pair=pair) for pair in self._pairs
        }

        # Optional callback for broadcasting updates
        self._on_tick_update: Optional[
            Callable[[RateUpdateMessage], Awaitable[None]]
        ] = None

    def set_update_callback(
        self,
        callback: Callable[[RateUpdateMessage], Awaitable[None]],
    ) -> None:
        """
        Register a callback to be executed whenever a new tick is ingested.

        Typical use case: send updates to a WebSocket ConnectionManager.
        """
        self._on_tick_update = callback

    async def load_initial_averages(self) -> None:
        """
        Load the latest hourly averages from the repository for all pairs.

        This is typically called on application startup so that the system
        starts with meaningful hourly_avg values even before new ticks arrive.
        """
        rows = await self._repo.get_latest_for_pairs(self._pairs)

        for row in rows:
            state = self._state.get(row.pair)
            if state is None:
                # Unknown pair from the database, ignore defensively.
                continue

            state.hour_start = row.hour_start
            state.hourly_avg = row.avg_price
            state.count = row.count
            # last_price / last_update will be filled as new ticks arrive

    async def ingest_tick(self, tick: InternalTick) -> None:
        """
        Process a new tick:

        - Update last price and last update timestamp
        - Update in-memory hourly aggregation
        - Persist the previous hour's average when we detect an hour change
        - Emit a RateUpdateMessage via the callback if configured
        """
        if tick.pair not in self._state:
            # Ignore unsupported pairs defensively.
            return

        state = self._state[tick.pair]
        normalized_ts = self._normalize_to_utc(tick.timestamp)
        hour_start = self._truncate_to_hour(normalized_ts)

        # Update last known price and timestamp
        state.last_price = tick.price
        state.last_update = normalized_ts

        # First tick ever for this pair
        if state.hour_start is None:
            state.hour_start = hour_start
            state.sum_prices = tick.price
            state.count = 1
            state.hourly_avg = tick.price

            await self._emit_update(state)
            return

        # Same hour: update running average
        if hour_start == state.hour_start:
            state.sum_prices += tick.price
            state.count += 1
            state.hourly_avg = state.sum_prices / state.count

            await self._emit_update(state)
            return

        # Hour changed: persist the previous hour and start a new bucket
        await self._persist_current_hour(state)

        # Initialize new hour bucket
        state.hour_start = hour_start
        state.sum_prices = tick.price
        state.count = 1
        state.hourly_avg = tick.price

        await self._emit_update(state)

    async def _persist_current_hour(self, state: PairRuntimeState) -> None:
        """
        Persist the current hour's aggregation for the given pair, if valid.
        """
        if state.hour_start is None or state.hourly_avg is None or state.count <= 0:
            return

        await self._repo.save(
            pair=state.pair,
            hour_start=state.hour_start,
            avg_price=state.hourly_avg,
            count=state.count,
        )

    async def _emit_update(self, state: PairRuntimeState) -> None:
        """
        Build and emit a RateUpdateMessage using the configured callback,
        if any. This keeps the broadcast logic decoupled from the core
        aggregation logic.
        """
        if self._on_tick_update is None:
            return

        if state.last_price is None or state.last_update is None:
            # Not enough information to build a meaningful update.
            return

        # hourly_avg can be None only in very edge cases; we guard anyway.
        hourly_avg = (
            state.hourly_avg if state.hourly_avg is not None else state.last_price
        )

        message = RateUpdateMessage(
            pair=state.pair,
            price=state.last_price,
            hourly_avg=hourly_avg,
            last_update=state.last_update,
        )

        await self._on_tick_update(message)

    def get_snapshot(self) -> List[PairPublicState]:
        """
        Build a snapshot of the current in-memory state for all pairs.

        This is used by the REST layer to return an initial view of the system.
        """
        snapshot: List[PairPublicState] = []

        for pair, state in self._state.items():
            snapshot.append(
                PairPublicState(
                    pair=pair,
                    price=state.last_price,
                    hourly_avg=state.hourly_avg,
                    last_update=state.last_update,
                )
            )

        return snapshot

    def get_pair_state(self, pair: str) -> Optional[PairPublicState]:
        """
        Return the current public state for a single pair, if known.
        """
        state = self._state.get(pair)
        if state is None:
            return None

        return PairPublicState(
            pair=pair,
            price=state.last_price,
            hourly_avg=state.hourly_avg,
            last_update=state.last_update,
        )

    @staticmethod
    def _normalize_to_utc(ts: datetime) -> datetime:
        """
        Ensure the timestamp is timezone-aware in UTC.

        Finnhub typically sends epoch timestamps in UTC, but we normalize
        defensively in case different sources are used in the future.
        """
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    @staticmethod
    def _truncate_to_hour(ts: datetime) -> datetime:
        """
        Truncate a UTC datetime to the beginning of the hour.
        """
        return ts.replace(minute=0, second=0, microsecond=0)
