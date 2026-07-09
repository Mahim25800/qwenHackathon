import React, { useEffect, useMemo, useState } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { AgentNode } from './AgentNode';
import { DataEdge } from './DataEdge';
import { useAppStore } from '../lib/store';

const nodeTypes = {
  agent: AgentNode,
};

const edgeTypes = {
  data: DataEdge,
};

export function AgentTopology() {
  const { agents, swarmState, currentIteration, finalResult } = useAppStore();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    // Generate nodes based on agent state
    const initialNodes = [
      {
        id: 'explorer',
        type: 'agent',
        position: { x: 250, y: 50 },
        data: {
          label: 'Data Explorer',
          role: 'Dataset Analyst',
          type: 'explorer',
          status: agents.explorer.status,
          output: agents.explorer.output ? 'Generated dataset profile' : undefined,
        },
      },
      {
        id: 'architect',
        type: 'agent',
        position: { x: 100, y: 250 },
        data: {
          label: 'Architect',
          role: 'Model Designer',
          type: 'architect',
          status: agents.architect.status,
          output: agents.architect.output ? `Iteration ${currentIteration} model ready` : undefined,
        },
      },
      {
        id: 'critic',
        type: 'agent',
        position: { x: 400, y: 250 },
        data: {
          label: 'Critic',
          role: 'Sandbox Evaluator',
          type: 'critic',
          status: agents.critic.status,
          output: agents.critic.output ? `Evaluated Iteration ${currentIteration}` : undefined,
        },
      },
      {
        id: 'end',
        position: { x: 250, y: 450 },
        data: { label: swarmState === 'completed' ? (finalResult?.final_status === 'approved' ? 'Success' : 'Fallback') : 'END' },
        style: {
          background: swarmState === 'completed' 
            ? (finalResult?.final_status === 'approved' ? 'rgba(0,255,100,0.2)' : 'rgba(255,150,0,0.2)') 
            : 'rgba(255,255,255,0.05)',
          color: 'white',
          border: swarmState === 'completed' 
            ? (finalResult?.final_status === 'approved' ? '1px solid rgba(0,255,100,0.5)' : '1px solid rgba(255,150,0,0.5)') 
            : '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '10px 20px',
        },
      },
    ] as Node[];

    setNodes(initialNodes);

    // Generate edges
    const isExplorerActive = agents.explorer.active || (agents.explorer.status === 'completed' && agents.architect.status === 'idle' && swarmState !== 'completed');
    const isArchitectActive = agents.architect.active || (agents.architect.status === 'completed' && agents.critic.status === 'idle' && swarmState !== 'completed');
    const isCriticActive = agents.critic.active;
    const isCriticReject = agents.critic.output?.status === 'REJECT' && agents.architect.status === 'thinking';
    const isCriticApprove = agents.critic.output?.status === 'APPROVE' && swarmState === 'completed';

    const initialEdges = [
      {
        id: 'e-to-a',
        source: 'explorer',
        target: 'architect',
        type: 'data',
        animated: isExplorerActive,
        data: { active: isExplorerActive, color: 'var(--color-explorer-end)' },
        markerEnd: { type: MarkerType.ArrowClosed, color: isExplorerActive ? 'var(--color-explorer-end)' : 'rgba(255,255,255,0.2)' },
      },
      {
        id: 'a-to-c',
        source: 'architect',
        target: 'critic',
        type: 'data',
        animated: isArchitectActive,
        data: { active: isArchitectActive, color: 'var(--color-architect-end)' },
        markerEnd: { type: MarkerType.ArrowClosed, color: isArchitectActive ? 'var(--color-architect-end)' : 'rgba(255,255,255,0.2)' },
      },
      {
        id: 'c-to-a',
        source: 'critic',
        sourceHandle: 'loop',
        target: 'architect',
        targetHandle: 'loop',
        type: 'data',
        animated: isCriticReject,
        data: { active: isCriticReject, reject: true, color: 'var(--color-critic-end)' },
        markerEnd: { type: MarkerType.ArrowClosed, color: isCriticReject ? 'var(--color-critic-end)' : 'rgba(255,255,255,0.2)' },
      },
      {
        id: 'c-to-end',
        source: 'critic',
        target: 'end',
        type: 'data',
        animated: isCriticApprove,
        data: { active: isCriticApprove, color: 'rgba(0,255,100,0.8)' },
        markerEnd: { type: MarkerType.ArrowClosed, color: isCriticApprove ? 'rgba(0,255,100,0.8)' : 'rgba(255,255,255,0.2)' },
      },
    ] as Edge[];

    setEdges(initialEdges);
  }, [agents, swarmState, currentIteration, finalResult]);

  return (
    <div className="w-full h-full relative" style={{ minHeight: '400px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        attributionPosition="bottom-right"
        className="dark"
      >
        <Background color="rgba(255,255,255,0.05)" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}
