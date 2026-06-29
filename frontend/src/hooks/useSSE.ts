import { useEffect, useState, useCallback } from 'react';
import { useAppStore, AppState } from '../lib/store';
import { SwarmEvent } from '../lib/types';

export function useSSE() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const store = useAppStore();

  const connect = useCallback((id: string) => {
    setSessionId(id);
  }, []);

  const disconnect = useCallback(() => {
    setSessionId(null);
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    const eventSource = new EventSource(`${API_BASE_URL}/swarm/stream/${sessionId}`);

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsConnected(false);
        return;
      }

      try {
        const data: SwarmEvent = JSON.parse(event.data);
        handleSwarmEvent(data, store);
      } catch (err) {
        console.error('Failed to parse SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      store.setSwarmState('error', 'Connection to server lost.');
      eventSource.close();
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [sessionId]);

  return { connect, disconnect, isConnected };
}

function handleSwarmEvent(event: SwarmEvent, store: AppState) {
  if (event.iteration) {
    store.setIteration(event.iteration);
  }

  // Common debate entry logic
  if (event.type === 'agent_result' || event.type === 'iteration_complete' || event.type === 'swarm_complete') {
    store.addDebateEntry({
      id: Math.random().toString(36).substring(7),
      agent: event.agent || 'system',
      action: event.type,
      data: event.data,
      message: event.message,
      timestamp: event.timestamp,
      iteration: event.iteration || store.currentIteration,
    });
  }

  switch (event.type) {
    case 'swarm_started':
      store.setSwarmState('running');
      break;

    case 'agent_thinking':
      if (event.agent) {
        store.updateAgent(event.agent, { status: 'thinking', active: true });
        // Set others to idle
        ['explorer', 'architect', 'critic'].forEach(a => {
          if (a !== event.agent) store.updateAgent(a, { status: 'idle', active: false });
        });
      }
      break;

    case 'agent_result':
      if (event.agent) {
        const agentName = event.agent === 'data_explorer' ? 'explorer' : event.agent;
        store.updateAgent(agentName, { status: 'completed', output: event.data });
        
        // Specific logic for when architect returns code
        if (agentName === 'architect' && event.data.pytorch_code) {
          store.setCurrentCode(event.data.pytorch_code);
        }
      }
      break;

    case 'iteration_complete':
      store.updateAgent('critic', { status: 'idle', active: false });
      break;

    case 'swarm_complete':
      store.setSwarmState('completed');
      store.setFinalResult(event.data);
      // Set all agents to idle
      ['explorer', 'architect', 'critic'].forEach(a => {
        store.updateAgent(a, { status: 'idle', active: false });
      });
      break;

    case 'error':
      store.setSwarmState('error', event.message);
      break;
  }
}
