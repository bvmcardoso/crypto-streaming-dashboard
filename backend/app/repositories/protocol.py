from typing import Protocol, Iterable, List
from datetime import datetime
from app.schemas.rates import PairSymbol, PairState, RatesSnapshot, RateUpdateMessage
from app.models.hourly_average import HourlyAverage


class HourlyAverageRepository(Protocol):
    """Abstraction for persisting and querying hourly averages"""

    async def save(
        self, pair: str, hour_start: datetime, avg_price: float, count: int
    ) -> HourlyAverage:
        """Persist a new hourly average entry"""
        raise NotImplementedError

    async def get_latest_for_pairs(self, pairs: Iterable[str]) -> List[HourlyAverage]:
        raise NotImplementedError
