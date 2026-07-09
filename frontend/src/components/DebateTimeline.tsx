import React, { useEffect, useRef } from 'react';
import { useAppStore } from '../lib/store';

export function DebateTimeline() {
  const { debateLog, swarmConfig } = useAppStore();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [debateLog]);

  return (
    <div className="glass-panel h-full flex flex-col w-full">
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20">
        <h2 className="text-sm font-bold text-white/90">Debate Log</h2>
        <span className="text-xs font-mono text-white/50">{debateLog.length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 custom-scrollbar">
        {debateLog.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-white/30 text-sm italic">
            Launch swarm to begin...
          </div>
        ) : (
          debateLog.map((entry, i) => (
            <div key={entry.id} className="relative pl-6">
              {/* Timeline line */}
              {i !== debateLog.length - 1 && (
                <div className="absolute left-2.5 top-6 bottom-[-24px] w-px bg-white/10"></div>
              )}
              
              {/* Timeline dot */}
              <div 
                className="absolute left-1 top-1.5 w-3 h-3 rounded-full border-2 border-[#0a0a0f]"
                style={{ background: `var(--color-${entry.agent === 'system' ? 'architect' : entry.agent}-start)` }}
              ></div>

              <div className="glass-panel p-3 text-sm">
                <div className="flex justify-between items-start mb-2">
                  <div className="font-bold capitalize text-white/90">
                    {entry.agent} <span className="text-white/40 font-normal text-xs ml-2">Iter {Math.min(entry.iteration, swarmConfig?.max_iterations || 5)}</span>
                  </div>
                  <div className="text-[10px] text-white/40 font-mono">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                <div className="text-white/70 mb-2">{entry.message || entry.action}</div>

                {entry.data && entry.data.status && (
                  <div className={`inline-block px-2 py-1 rounded text-xs font-bold mb-2 border ${
                    entry.data.status === 'APPROVE' || entry.data.status === 'approved'
                      ? 'bg-green-500/20 text-green-400 border-green-500/30'
                      : entry.data.status === 'max_iterations' || entry.data.status === 'running'
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                      : 'bg-red-500/20 text-red-400 border-red-500/30'
                  }`}>
                    {entry.data.status}
                  </div>
                )}

                {entry.data && (
                  <details className="mt-2 group">
                    <summary className="text-xs text-white/40 cursor-pointer hover:text-white/70 transition-colors">View Data</summary>
                    <div className="mt-2 bg-black/50 p-2 rounded border border-white/5 overflow-x-auto">
                      <pre className="text-[10px] text-white/60 font-mono m-0">
                        {JSON.stringify(entry.data, null, 2)}
                      </pre>
                    </div>
                  </details>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
