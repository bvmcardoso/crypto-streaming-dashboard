import { useEffect, useState } from 'react';
import type { PairState, RateUpdateMessage, PricePoint } from '../types/rates';
import { fetchRatesSnapshot } from '../api/rates';

type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'closed' | 'error';

interface UseRatesStreamResult {
  rates: PairState[];
  connectionStatus: ConnectionStatus;
  error: string | null;
}

const MAX_POINTS = 40;

// When we load from REST, we don't have history yet.
// We just attach an empty history array.
function fromSnapshot(snapshot: Omit<PairState, 'history'>[]): PairState[] {
  return snapshot.map((s) => ({
    ...s,
    history: [],
  }));
}

// Add a new point to the pair history and trim to MAX_POINTS.
function appendHistoryPoint(current: PairState[], update: RateUpdateMessage): PairState[] {
  const point: PricePoint = {
    timestamp: update.last_update,
    price: update.price,
  };

  return current.map((pair) => {
    if (pair.pair !== update.pair) {
      return pair;
    }

    const nextHistory = [...pair.history, point];
    if (nextHistory.length > MAX_POINTS) {
      nextHistory.splice(0, nextHistory.length - MAX_POINTS);
    }

    return {
      ...pair,
      price: update.price,
      hourly_avg: update.hourly_avg,
      last_update: update.last_update,
      history: nextHistory,
    };
  });
}

export function useRatesStream(): UseRatesStreamResult {
  const [rates, setRates] = useState<PairState[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;

    async function start() {
      try {
        const snapshot = await fetchRatesSnapshot();
        setRates(fromSnapshot(snapshot as any));
      } catch (err) {
        console.error('Failed to fetch initial snapshot:', err);
        setError('Failed to load initial rates.');
      }

      setConnectionStatus('connecting');

      const wsUrl = (import.meta.env.VITE_WS_BASE_URL ?? 'ws://127.0.0.1:8000') + '/ws/rates';

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setConnectionStatus('connected');
          setError(null);
        };

        ws.onmessage = (event: MessageEvent<string>) => {
          try {
            const msg: RateUpdateMessage = JSON.parse(event.data);
            setRates((prev) => appendHistoryPoint(prev, msg));
          } catch (parseErr) {
            console.error('Failed to parse WebSocket message:', parseErr);
          }
        };

        ws.onerror = (event) => {
          console.error('WebSocket error:', event);
          setConnectionStatus('error');
          setError('WebSocket connection error.');
        };

        ws.onclose = () => {
          setConnectionStatus('closed');
        };
      } catch (wsErr) {
        console.error('Failed to open WebSocket:', wsErr);
        setConnectionStatus('error');
        setError('Could not open WebSocket connection.');
      }
    }

    start();

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  return { rates, connectionStatus, error };
}
