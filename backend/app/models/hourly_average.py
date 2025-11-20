from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HourlyAverage(Base):
    __tablename__ = "hourly_averages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    hour_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index(
            "ix_hourly_averages_pair_hour_start",
            "pair",
            "hour_start",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"HourlyAverage(id={self.id!r}, pair={self.pair!r})"
            f"hour_start={self.hour_start!r}, avg_price={self.avg_price!r})"
            f"count={self.count!r}"
        )
