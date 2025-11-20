# Crypto Streaming Dashboard

Real-time Ethereum pair dashboard running fully in Docker. FastAPI backend + React frontend with real-time WebSocket updates.

## Environment Setup (Backend)

Before running anything, you must configure your Finnhub API key.

1. Git clone this repository.

2. Inside the `backend/` folder, copy the example environment file:

```bash
cp backend/.env.example backend/.env
```

3. Open `backend/.env` and insert **your own** Finnhub API key:

```env
FINNHUB_API_KEY=your_key_here
```

This key is required for the real-time streaming data.

## Architecture

### Backend (FastAPI)
- REST endpoint for initial snapshot  
- WebSocket endpoint for continuous price updates  
- In-memory aggregation service (ticks + hourly averages)  
- Clean structure: API → Service → Repository → Domain

### Frontend (React + TypeScript)
- `useRatesStream` merges REST + WebSocket sources  
- Tracks connection lifecycle (open / closed / reconnecting)  
- UI updates instantly with minimal re-renders  

## Data Flow

1. Frontend loads snapshot via `GET /api/v1/rates/current`  
2. Opens the WebSocket at `/ws/rates`  
3. Backend streams rate updates  
4. React merges updates in real time to update the dashboard  

## Running (Docker Only)

No local Python or Node setup required.

### Start full stack

```bash
make docker-up
```

Once it starts:

- **Frontend**: http://localhost:5173  
- **Backend API Docs**: http://localhost:8000/docs  

### Stop

```bash
make docker-down
```

### Restart

```bash
make docker-restart
```

## Backend Tests

Tests run inside Docker:

```bash
make backend-tests
```

Tests cover:

- Tick ingestion  
- Hour rollover + average computation  
- Independent pair state tracking  

## Developer Commands

### Backend shell

```bash
make backend-shell
```

### Frontend shell

```bash
make frontend-shell
```

## Tech Choices

- FastAPI for the high-throughput backend  
- Pydantic for typed validation  
- WebSockets for real-time updates  
- React + TypeScript for predictable UI state  
- Docker for deterministic runtime  
