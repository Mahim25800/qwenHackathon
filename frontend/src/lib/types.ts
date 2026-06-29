export type AgentStatus = 'idle' | 'thinking' | 'completed' | 'error';
export type CritiqueStatus = 'APPROVE' | 'REJECT';

export interface DatasetProfile {
  name: string;
  input_shape: number[];
  num_classes: number;
  num_samples: number;
  data_characteristics: string;
  theoretical_bounds: {
    max_pooling_layers: number;
    min_receptive_field: number;
  };
  recommended_architectures: string[];
}

export interface ModelBlueprint {
  architecture_name: string;
  total_params: number;
  total_macs?: number;
  pytorch_code: string;
  layers: Array<{name: string; type: string; params: number}>;
}

export interface CritiqueMatrix {
  status: CritiqueStatus;
  param_count: number;
  mac_count?: number;
  estimated_latency_ms?: number;
  bottleneck_layer?: string;
  reason: string;
  suggestion?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface SwarmEvent {
  type: 'swarm_started' | 'agent_thinking' | 'agent_result' | 'iteration_complete' | 'swarm_complete' | 'error';
  agent?: string;
  data: any;
  timestamp: string;
  message?: string;
  iteration?: number;
}

export interface DebateEntry {
  id: string;
  agent: string;
  action: string;
  data: any;
  message?: string;
  timestamp: string;
  iteration: number;
}

export interface SwarmConfig {
  dataset_name: string;
  input_shape: number[];
  num_classes: number;
  max_params: number;
  target_latency_ms: number;
  max_iterations: number;
  user_constraints?: string;
}
