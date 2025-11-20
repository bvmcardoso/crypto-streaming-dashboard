import { apiClient } from './client';
import type { PairState } from '../types/rates';

export interface RatesSnapshotResponse {
  pairs: PairState[];
}

// Fetch the initial snapshot of all pairs from the backend.
// This is used once when the dashboard mounts.
export async function fetchRatesSnapshot(): Promise<PairState[]> {
  const response = await apiClient.get<RatesSnapshotResponse>('/api/v1/rates/current');
  return response.data.pairs;
}
