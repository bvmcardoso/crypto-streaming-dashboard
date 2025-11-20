// Shape of a single trading pair returned by the REST snapshot
export interface PricePoint {
  timestamp: string; // ISO string
  price: number;
}

// State for a single pair on the frontend
export interface PairState {
  pair: string;
  price: number | null;
  hourly_avg: number | null;
  last_update: string | null; // ISO timestamp from backend
  history: PricePoint[]; // used only for charts
}

// Message format that arrives via WebSocket
export interface RateUpdateMessage {
  pair: string;
  price: number;
  hourly_avg: number;
  last_update: string;
}
