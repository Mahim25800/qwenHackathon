import React from 'react';
import { BaseEdge, EdgeProps, getBezierPath, Edge } from '@xyflow/react';

export type CustomEdgeData = {
  active?: boolean;
  reject?: boolean;
  color?: string;
};

export type CustomEdgeType = Edge<CustomEdgeData, 'data'>;

export function DataEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  animated,
  data
}: EdgeProps<CustomEdgeType>) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isActive = data?.active;
  const isReject = data?.reject;
  
  let strokeColor = 'rgba(255, 255, 255, 0.2)';
  if (isActive) {
    strokeColor = data?.color || 'rgba(255, 255, 255, 0.8)';
  } else if (isReject) {
    strokeColor = 'var(--color-critic-end)';
  }

  return (
    <>
      <BaseEdge 
        path={edgePath} 
        markerEnd={markerEnd} 
        style={{
          ...style,
          strokeWidth: isActive ? 3 : 2,
          stroke: strokeColor,
          strokeDasharray: isActive ? 'none' : '5,5',
          transition: 'all 0.3s ease',
          opacity: isActive ? 1 : 0.5,
        }} 
      />
      {isActive && (
        <circle r="4" fill="#fff" className="animate-particle">
          <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}
    </>
  );
}
