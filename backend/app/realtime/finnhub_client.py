from __future__ import annotations

import asyncio
import json
import logging
import os

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed
from app.services.rates_manager_service import RatesManagerService, InternalTick

logger = logging.getLogger(__name__)

# Mapping between our internal pairs and Finnhub symbols:
PAIR_TO_FINNHUB_SYMBOL: Dict[str, str] = {
    "ETH/USDC": "BINANCE:ETHUSDC",
    "ETH/USDT": "BINANCE:ETHUSDT",
    "ETH/BTC": "BINANCE:ETHBTC",
}


@dataclass
class FinnhubConfig:
    api_key: str
    base_url: str = "wss://ws.finnhub.io"
    reconnect_base_delay: float = 1.0
    reconnect_max_delay: float = 30.0


class FinnhubClient:
    """
    WebSocket client responsible for:
    - Connecting to Finnhub WebSocket API
    - Subscribing to ETH-related pairs
    - Receiving trade messages / converting them to InternalTick
    - Feeding ticks into the RatesManagerService
    - Handling reconnection
    """

    def __init__(
        self, rates_service: RatesManagerService, config: Optional[FinnhubConfig] = None
    ) -> None:
        api_key = os.getenv("FINNHUB_API_KEY")
        if not api_key:
            raise RuntimeError(
                "FINNHUB_API_KEY is not set. Please configure it in the environment."
            )

        self._config = config or FinnhubConfig(api_key=api_key)
        self._rates_service = rates_service
        self._stop_event = asyncio.Event()

    def build_ws_url(self) -> str:
        return f"{self._config.base_url}?token={self._config.api_key}"

    async def run_forever(self) -> None:
        """Keep websocket connection alive and reconnect on failures"""
        delay = self._config.reconnect_base_delay

        while not self._stop_event.is_set():
            try:
                await self._connect_and_listen()
                # If _connect_and_listen works properly, reset delay
                delay = self._config.reconnect_base_delay
            except asyncio.CancelledError:
                logger.info("FinnhubClient run_forever cancelled, stopping.")
                break
            except Exception as exc:
                logger.warning(
                    "FinnhubClient connection error: %s. Reconnecting in %.1fs",
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._config.reconnect_max_delay)

    async def _connect_and_listen(self) -> None:
        """Connect to Finnhub Websocket and listen for incoming messages"""
        url = self.build_ws_url()
        logger.info("Connecting to Finnhub WebSocket at %s", url)

        async with websockets.connect(url) as ws:
            logger.info("Connected to Finnhub WebSocket.")

            await self._subscribe_all(ws)

            async for raw in ws:
                if self._stop_event.is_set():
                    break
                await self._handle_message(raw)

        logger.info("Finnhub Websocket connection closed.")

    async def _subscribe_all(self, ws) -> None:
        """
        Subscribe to all configured symbols.
        """
        for pair, symbol in PAIR_TO_FINNHUB_SYMBOL.items():
            payload = {"type": "subscribe", "symbol": symbol}
            await ws.send(json.dumps(payload))
            logger.info("Subscribed to %s (%s)", pair, symbol)

    async def _handle_message(self, raw: str) -> None:
        """
        Handle a single raw JSON message from Finnhub.
        """
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON from Finnhub: %s", raw)
            return

        msg_type = message.get("type")
        if msg_type != "trade":
            # Ignore other message types (ping, etc.)
            return

        data = message.get("data") or []
        for trade in data:
            await self._handle_trade(trade)

    async def _handle_trade(self, trade: dict) -> None:
        """Convert a Finnhub trade dict into an InternalTick and pass it to the server
        Expected fields:
            s: symbol (e.g. 'BINANCE:ETHUSDT')
            p: price
            t: timestamp in milliseconds
        """
        symbol = trade.get("s")
        price = trade.get("p")
        ts_ms = trade.get("t")

        if symbol is None or price is None or ts_ms is None:
            logger.debug("Skipping incomplete trade payload: %s", trade)
            return

        pair = self._map_symbol_to_pair(symbol)
        if pair is None:
            # Not one of the pairs we care about
            return

        ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)

        tick = InternalTick(
            pair=pair,
            price=float(price),
            timestamp=ts,
        )

        await self._rates_service.ingest_tick(tick)

    @staticmethod
    def _map_symbol_to_pair(symbol: str) -> Optional[str]:
        """
        Map a Finnhub symbol (e.g. 'BINANCE:ETHUSDT') back to our internal pair.
        """
        for pair, finnhub_symbol in PAIR_TO_FINNHUB_SYMBOL.items():
            if symbol == finnhub_symbol:
                return pair
        return None

    async def stop(self) -> None:
        """
        Signal the client to stop and let run_forever() exit gracefully.
        """
        self._stop_event.set()
