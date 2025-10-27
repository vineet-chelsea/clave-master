/**
 * API Client for Backend Communication
 * Handles API endpoint configuration for different environments
 */

// API base URL - will be replaced during build time by Vite
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export const API_URL = `${API_BASE_URL}/api`;

/**
 * Get full API endpoint URL
 */
export function getApiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_URL}/${cleanEndpoint}`;
}

/**
 * Fetch from API with error handling
 */
export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  try {
    const url = getApiUrl(endpoint);
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Get latest sensor reading
 */
export async function getLatestSensorReading() {
  try {
    const data = await apiFetch<{
      pressure: number;
      temperature: number;
      timestamp: string;
    }>('sensor-readings/latest');
    
    return data;
  } catch (error) {
    console.error('Error fetching sensor reading:', error);
    return { pressure: 0, temperature: 25, timestamp: null };
  }
}

/**
 * Start manual control session
 */
export async function startManualControl(targetPressure: number, durationMinutes: number) {
  return apiFetch<{
    success: boolean;
    session_id: number;
    message: string;
    target_pressure: number;
    duration_minutes: number;
  }>('start-control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_pressure: targetPressure, duration_minutes: durationMinutes })
  });
}

/**
 * Start auto program
 */
export async function startAutoProgram(programId: number) {
  return apiFetch<{
    success: boolean;
    session_id: number;
    message: string;
  }>('start-auto-program', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ program_id: programId })
  });
}

/**
 * Get all sessions
 */
export async function getSessions() {
  return apiFetch<Array<{
    id: number;
    target_pressure: number;
    duration_minutes: number;
    status: string;
    start_time: string;
    end_time: string | null;
  }>>('sessions');
}

/**
 * Get active session
 */
export async function getActiveSession() {
  const sessions = await getSessions();
  return sessions.find(s => s.status === 'running' || s.status === 'paused') || null;
}

/**
 * Get programs list
 */
export async function getPrograms() {
  return apiFetch<Array<{
    id: number;
    name: string;
    steps_data: string;
  }>>('programs');
}

/**
 * Get session logs
 */
export async function getSessionLogs(sessionId: number) {
  return apiFetch<Array<{
    id: number;
    pressure: number;
    temperature: number;
    valve_position: number;
    timestamp: string;
  }>>(`sessions/${sessionId}/logs`);
}

/**
 * Pause control
 */
export async function pauseControl() {
  return apiFetch('pause-control', { method: 'POST' });
}

/**
 * Resume control
 */
export async function resumeControl() {
  return apiFetch('resume-control', { method: 'POST' });
}

/**
 * Stop control
 */
export async function stopControl() {
  return apiFetch('stop-control', { method: 'POST' });
}

