import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.rates.router import router as rates_router
from app.api.v1.ws.router import router as ws_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.container import get_rates_manager_service, get_connection_manager
from app.realtime.finnhub_client import FinnhubClient


@asynccontextmanager
async def lifespan(app):
    """
    - Initializes services and connection manager
    - Loads initial hourly averages
    - Starts Finnhub WebSocket client in the background
    - Cleans up on shutdown
    """
    from app.core.database import engine, Base

    # Create tables if they don't exist yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    rates_manager = get_rates_manager_service()
    connection_manager = get_connection_manager()

    # Load initial data from the database
    await rates_manager.load_initial_averages()

    # Attach callback so every tick trigger a Websocket broadcast
    rates_manager.set_update_callback(connection_manager.broadcast_rate_update)

    # Start Finnhub client in the background
    finnhub_client = FinnhubClient(rates_service=rates_manager)
    finnhub_task = asyncio.create_task(finnhub_client.run_forever())

    try:
        yield
    finally:
        # Shutdown Finnhub client gracefully
        finnhub_task.cancel()
        try:
            await finnhub_task
        except Exception:
            pass


app = FastAPI(
    title="Crypto Streaming Dashboard API", version="1.0.0", lifespan=lifespan
)

# REST routes
app.include_router(rates_router, prefix="/api/v1/rates", tags=["rates"])

# Websocket routes
app.include_router(
    ws_router,
    prefix="/ws",
    tags=["ws"],
)

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # only this origin is allowed
    allow_credentials=True,
    allow_methods=["*"],  # or restrict to specific methods like ["GET", "POST"]
    allow_headers=["*"],  # or restrict to specific headers if needed
)
