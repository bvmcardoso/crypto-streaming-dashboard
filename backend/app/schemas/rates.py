from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Literal
from pydantic import BaseModel


class PairSymbol(str, Enum):
    ETH_USDC = "ETH/USDC"
    ETH_USDT = "ETH/USDT"
    ETH_BTC = "ETH/BTC"


class PairState(BaseModel):
    pair: PairSymbol
    price: float | None = None
    hourly_avg: float | None = None
    last_update: datetime | None = None


class RatesSnapshot(BaseModel):
    """REST endpoint response: api/v1/rates/current"""

    pairs: List[PairState]


class RateUpdateMessage(BaseModel):
    """Message sent via WebSocket for each price update"""

    type: Literal["rate_update"] = "rate_update"
    pair: PairSymbol
    price: float
    hourly_avg: float
    last_update: datetime
