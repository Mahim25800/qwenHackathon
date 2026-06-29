import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { AgentStatus, SwarmConfig, DebateEntry, SwarmEvent } from './types';

interface AgentState {
  status: AgentStatus;
  active: boolean;
  output?: any;
}

export interface AppState {
  swarmState: 'idle' | 'running' | 'completed' | 'error';
  agents: Record<string, AgentState>;
  debateLog: DebateEntry[];
  currentCode: string;
  currentIteration: number;
  finalResult: any | null;
  swarmConfig: SwarmConfig;
  error: string | null;
  sessionId: string | null;

  // Actions
  startSwarm: (config: SwarmConfig) => void;
  updateAgent: (agentId: string, updates: Partial<AgentState>) => void;
  addDebateEntry: (entry: DebateEntry) => void;
  setCurrentCode: (code: string) => void;
  setIteration: (iteration: number) => void;
  setFinalResult: (result: any) => void;
  setSwarmState: (state: 'idle' | 'running' | 'completed' | 'error', error?: string) => void;
  setSessionId: (id: string | null) => void;
  reset: () => void;
}

const initialConfig: SwarmConfig = {
  dataset_name: 'CIFAR-10',
  input_shape: [3, 32, 32],
  num_classes: 10,
  max_params: 10000000,
  target_latency_ms: 20,
  max_iterations: 5,
};

const initialAgentsState = {
  explorer: { status: 'idle' as AgentStatus, active: false },
  architect: { status: 'idle' as AgentStatus, active: false },
  critic: { status: 'idle' as AgentStatus, active: false },
};

export const useAppStore = create<AppState>()(
  subscribeWithSelector((set) => ({
    swarmState: 'idle',
    agents: initialAgentsState,
    debateLog: [],
    currentCode: '',
    currentIteration: 0,
    finalResult: null,
    swarmConfig: initialConfig,
    error: null,
    sessionId: null,

    startSwarm: (config) =>
      set({
        swarmState: 'running',
        swarmConfig: config,
        agents: {
          explorer: { status: 'thinking', active: true },
          architect: { status: 'idle', active: false },
          critic: { status: 'idle', active: false },
        },
        debateLog: [],
        currentCode: '',
        currentIteration: 1,
        finalResult: null,
        error: null,
      }),

    updateAgent: (agentId, updates) =>
      set((state) => ({
        agents: {
          ...state.agents,
          [agentId]: { ...state.agents[agentId], ...updates },
        },
      })),

    addDebateEntry: (entry) =>
      set((state) => ({
        debateLog: [...state.debateLog, entry],
      })),

    setCurrentCode: (code) =>
      set({ currentCode: code }),

    setIteration: (iteration) =>
      set({ currentIteration: iteration }),

    setFinalResult: (result) =>
      set({ finalResult: result }),

    setSwarmState: (swarmState, error = undefined) =>
      set({ swarmState, error }),

    setSessionId: (id) =>
      set({ sessionId: id }),

    reset: () =>
      set({
        swarmState: 'idle',
        agents: initialAgentsState,
        debateLog: [],
        currentCode: '',
        currentIteration: 0,
        finalResult: null,
        error: null,
        sessionId: null,
      }),
  }))
);
