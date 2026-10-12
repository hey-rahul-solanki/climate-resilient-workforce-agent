/**
 * API types for HTTP communication between frontend and backend.
 */

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
  message?: string;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'checking';

export interface BackendHealth {
  status: ConnectionStatus;
  url: string;
  timestamp: string;
  latencyMs?: number;
  message?: string;
  version?: string;
}

export interface ApiConfig {
  baseUrl: string;
  timeoutMs?: number;
}
