import React from 'react';

interface MetricsCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}

export function MetricsCard({ label, value, unit, trend, color = 'var(--color-architect-end)' }: MetricsCardProps) {
  return (
    <div className="glass-panel p-4 flex flex-col justify-between relative overflow-hidden group">
      <div 
        className="absolute top-0 left-0 w-1 h-full opacity-50"
        style={{ background: color }}
      ></div>
      
      <div className="text-[10px] uppercase tracking-wider text-white/50 mb-1">{label}</div>
      <div className="flex items-baseline gap-1">
        <div className="text-2xl font-bold text-white/90 font-mono">{value}</div>
        {unit && <div className="text-xs text-white/40">{unit}</div>}
      </div>
      
      {trend && (
        <div className="absolute top-4 right-4">
          {trend === 'down' && <span className="text-green-400">↓</span>}
          {trend === 'up' && <span className="text-red-400">↑</span>}
          {trend === 'neutral' && <span className="text-white/30">-</span>}
        </div>
      )}
    </div>
  );
}
