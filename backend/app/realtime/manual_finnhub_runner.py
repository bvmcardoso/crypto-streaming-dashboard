from __future__ import annotations

import asyncio
import logging

from app.realtime.finnhub_client import FinnhubClient, InternalTick


logger = logging.getLogger(__name__)


class DummyRatesService:
    """
    Minimal stand-in for RatesManagerService, used only for manual testing.

    It just logs incoming ticks instead of doing any aggregation or persistence.
    """

    async def ingest_tick(self, tick: InternalTick) -> None:
        logger.info(
            "Received tick: pair=%s price=%s ts=%s",
            tick.pair,
            tick.price,
            tick.timestamp,
        )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    service = DummyRatesService()
    client = FinnhubClient(rates_service=service)

    # Run the client until you Ctrl+C
    await client.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Manual Finnhub runner stopped by user.")
