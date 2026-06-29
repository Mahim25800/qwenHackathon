import { memo } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import { AgentStatus } from '../lib/types';

export type AgentNodeData = {
  label: string;
  role: string;
  status: AgentStatus;
  type: 'explorer' | 'architect' | 'critic';
  output?: string;
};

export type AgentNodeType = Node<AgentNodeData, 'agent'>;

export const AgentNode = memo(({ id, data, isConnectable }: NodeProps<AgentNodeType>) => {
  const isThinking = data.status === 'thinking';
  
  let glowColor = '';
  if (data.type === 'explorer') glowColor = 'var(--color-explorer-end)';
  if (data.type === 'architect') glowColor = 'var(--color-architect-end)';
  if (data.type === 'critic') glowColor = 'var(--color-critic-end)';

  return (
    <div 
      className={`glass-panel p-4 min-w-[220px] transition-all duration-300 relative`}
      style={{
        boxShadow: isThinking ? `0 0 20px 2px ${glowColor}40` : '',
        borderColor: isThinking ? glowColor : 'var(--glass-border)',
      }}
    >
      <Handle type="target" position={Position.Top} isConnectable={isConnectable} style={{ background: glowColor, border: 'none' }} />
      
      <div className="flex items-center gap-3 mb-3">
        <div 
          className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white shadow-lg"
          style={{ background: `linear-gradient(135deg, var(--color-${data.type}-start), var(--color-${data.type}-end))` }}
        >
          {data.label.charAt(0)}
        </div>
        <div>
          <div className="text-sm font-bold">{data.label}</div>
          <div className="text-xs text-white/50 uppercase tracking-wider">{data.role}</div>
        </div>
      </div>
      
      <div className="bg-black/30 rounded-lg p-3 text-xs min-h-[60px] border border-white/5 relative">
        {isThinking ? (
          <div className="flex items-center gap-2 text-white/70">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-current rounded-full" style={{ animation: 'pulse-dot 1s infinite', animationDelay: '0s' }}></span>
              <span className="w-1.5 h-1.5 bg-current rounded-full" style={{ animation: 'pulse-dot 1s infinite', animationDelay: '0.2s' }}></span>
              <span className="w-1.5 h-1.5 bg-current rounded-full" style={{ animation: 'pulse-dot 1s infinite', animationDelay: '0.4s' }}></span>
            </div>
            Thinking...
          </div>
        ) : data.output ? (
          <div className="text-white/80 line-clamp-3 font-mono">{data.output}</div>
        ) : (
          <div className="text-white/30 italic">Waiting...</div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} isConnectable={isConnectable} style={{ background: glowColor, border: 'none' }} />
      {data.type === 'critic' && (
        <Handle type="source" position={Position.Left} id="loop" isConnectable={isConnectable} style={{ background: glowColor, border: 'none' }} />
      )}
      {data.type === 'architect' && (
        <Handle type="target" position={Position.Right} id="loop" isConnectable={isConnectable} style={{ background: glowColor, border: 'none' }} />
      )}
    </div>
  );
});

AgentNode.displayName = 'AgentNode';
