from fastapi import APIRouter, Depends
from typing import List

from app.api.deps import get_rates_manager
from app.schemas.rates import RatesSnapshot, PairState
from app.services.rates_manager_service import RatesManagerService

router = APIRouter()


@router.get("/current", response_model=RatesSnapshot)
async def get_current_rates(
    rates_manager: RatesManagerService = Depends(get_rates_manager),
) -> RatesSnapshot:
    snapshot = rates_manager.get_snapshot()

    pairs: List[PairState] = [
        PairState(
            pair=item.pair,
            price=item.price,
            hourly_avg=item.hourly_avg,
            last_update=item.last_update,
        )
        for item in snapshot
    ]

    return RatesSnapshot(pairs=pairs)
