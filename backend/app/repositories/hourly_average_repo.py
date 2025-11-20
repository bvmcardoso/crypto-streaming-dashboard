from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Sequence

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.hourly_average import HourlyAverage
from app.repositories.protocol import HourlyAverageRepository


class SqlAlchemyHourlyAverageRepository(HourlyAverageRepository):
    """SQLAlchemy-based implementation for HourlyAverageRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(
        self,
        pair: str,
        hour_start: datetime,
        avg_price: float,
        count: int,
    ) -> None:
        """
        Insert or update a row for the given (pair, hour_start)
        This method is idempotent: Calling it multiple times will simply overwrite the stored average and count
        """
        async with self._session_factory() as session:
            async with session.begin():  # it handles commit
                stmt: Select[tuple[HourlyAverage]] = select(HourlyAverage).where(
                    (HourlyAverage.pair == pair)
                    & (HourlyAverage.hour_start == hour_start)
                )
                result = await session.execute(stmt)
                existing: HourlyAverage | None = result.scalar_one_or_none()

                if existing is None:
                    # Insert new row
                    obj = HourlyAverage(
                        pair=pair,
                        hour_start=hour_start,
                        avg_price=avg_price,
                        count=count,
                    )
                    session.add(obj)
                else:
                    # Update existing row
                    existing.avg_price = avg_price
                    existing.count = count

    async def get_latest_for_pairs(
        self,
        pairs: Iterable[str],
    ) -> List[HourlyAverage]:
        pair_list: List[str] = list(pairs)
        if not pair_list:
            return []

        async with self._session_factory() as session:
            stmt: Select[tuple[HourlyAverage]] = select(HourlyAverage).where(
                HourlyAverage.pair.in_(list(pairs))
            )
            result = await session.execute(stmt)
            rows: Sequence[HourlyAverage] = result.scalars().all()

        latest_by_pair: dict[str, HourlyAverage] = {}

        for row in rows:
            current = latest_by_pair.get(row.pair)
            if current is None or row.hour_start > current.hour_start:
                latest_by_pair[row.pair] = row

        return list(latest_by_pair.values())
