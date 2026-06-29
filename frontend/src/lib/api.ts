import { SwarmConfig } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function startSwarmSession(config: SwarmConfig): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/swarm/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error(`Failed to start swarm: ${response.statusText}`);
  }

  const data = await response.json();
  return data.session_id;
}
