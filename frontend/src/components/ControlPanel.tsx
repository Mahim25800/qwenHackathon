import React, { useState } from 'react';
import { useAppStore } from '../lib/store';
import { SwarmConfig } from '../lib/types';
import { startSwarmSession } from '../lib/api';
import { useSSE } from '../hooks/useSSE';

export function ControlPanel() {
  const { swarmState, swarmConfig, reset, setSwarmState, sessionId, setSessionId, agents } = useAppStore();
  const { connect, disconnect } = useSSE();
  
  const [config, setConfig] = useState<SwarmConfig>(swarmConfig);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (swarmState === 'running') return;
    
    setIsSubmitting(true);
    reset();
    
    try {
      // Connect to SSE first (in reality, backend generates ID, we connect, then start. 
      // Simplified here: backend returns session ID on start, then we connect.)
      const newSessionId = await startSwarmSession(config);
      setSessionId(newSessionId);
      connect(newSessionId);
    } catch (err) {
      console.error(err);
      setSwarmState('error', err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = async () => {
    if (swarmState === 'running' && sessionId) {
      try {
        await fetch(`http://127.0.0.1:8000/api/swarm/stop/${sessionId}`, { method: 'POST' });
      } catch (err) {
        console.error("Failed to stop session on backend:", err);
      }
    }
    disconnect();
    reset();
  };

  const isRunning = swarmState === 'running' || isSubmitting;

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <h2 className="text-xl font-bold mb-6 text-white/90 border-b border-white/10 pb-4">Configuration</h2>
      
      <form onSubmit={handleStart} className="flex flex-col gap-4 flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">
        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">Dataset</label>
          <select 
            value={config.dataset_name}
            onChange={(e) => {
              const dataset = e.target.value;
              let inputShape = [3, 32, 32];
              let numClasses = 10;
              if (dataset === 'MNIST' || dataset === 'Fashion-MNIST') {
                inputShape = [1, 28, 28];
              }
              setConfig({
                ...config, 
                dataset_name: dataset,
                input_shape: inputShape,
                num_classes: numClasses
              });
            }}
            disabled={isRunning}
            className="w-full bg-black/40 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-[var(--color-explorer-start)]"
          >
            <option value="CIFAR-10">CIFAR-10</option>
            <option value="MNIST">MNIST</option>
            <option value="Fashion-MNIST">Fashion-MNIST</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">Input Shape</label>
          <input 
            type="text" 
            value={config.input_shape.join(',')}
            onChange={(e) => setConfig({...config, input_shape: e.target.value.split(',').map(Number)})}
            disabled={isRunning}
            className="w-full bg-black/40 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-[var(--color-explorer-start)]"
            placeholder="e.g., 3,32,32"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">Max Parameters</label>
          <div className="flex items-center gap-3">
            <input 
              type="range" 
              min="100000" 
              max="20000000" 
              step="100000"
              value={config.max_params}
              onChange={(e) => setConfig({...config, max_params: Number(e.target.value)})}
              disabled={isRunning}
              className="flex-1 accent-[var(--color-architect-start)]"
            />
            <span className="text-xs font-mono w-16 text-right">{(config.max_params / 1000000).toFixed(1)}M</span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">Search Mode</label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setConfig({...config, max_iterations: 5})}
              disabled={isRunning}
              className={`flex-1 p-2 border rounded-md text-sm text-left transition-colors ${config.max_iterations === 5 || !config.max_iterations ? 'bg-white/10 border-[var(--color-explorer-start)] text-white' : 'border-white/10 text-white/50 hover:bg-white/5'}`}
            >
              <div className="font-bold flex items-center gap-2">
                <span className={config.max_iterations === 5 || !config.max_iterations ? 'text-green-400' : ''}>
                  {config.max_iterations === 5 || !config.max_iterations ? '☑️' : '☐'}
                </span>
                Standard Mode
              </div>
              <div className="text-[10px] mt-1 opacity-70">5 iterations, ~30 sec</div>
            </button>
            <button
              type="button"
              onClick={() => setConfig({...config, max_iterations: 10})}
              disabled={isRunning}
              className={`flex-1 p-2 border rounded-md text-sm text-left transition-colors ${config.max_iterations === 10 ? 'bg-white/10 border-[var(--color-explorer-start)] text-white' : 'border-white/10 text-white/50 hover:bg-white/5'}`}
            >
              <div className="font-bold flex items-center gap-2">
                <span className={config.max_iterations === 10 ? 'text-green-400' : ''}>
                  {config.max_iterations === 10 ? '☑️' : '☐'}
                </span>
                Deep Search
              </div>
              <div className="text-[10px] mt-1 opacity-70">10 iterations, higher cost</div>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">Target Latency (ms)</label>
          <input 
            type="number" 
            value={config.target_latency_ms}
            onChange={(e) => setConfig({...config, target_latency_ms: Number(e.target.value)})}
            disabled={isRunning}
            className="w-full bg-black/40 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-[var(--color-explorer-start)]"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-white/50 mb-1 uppercase tracking-wider">User Constraints (Optional)</label>
          <textarea 
            value={config.user_constraints || ""}
            onChange={(e) => setConfig({...config, user_constraints: e.target.value})}
            disabled={isRunning}
            rows={2}
            className="w-full bg-black/40 border border-white/10 rounded-md p-2 text-sm text-white focus:outline-none focus:border-[var(--color-architect-start)] resize-none"
            placeholder="e.g., Must use a CNN, optimize for memory, no pooling layers..."
          />
        </div>

        <div className="mt-auto pt-4 flex flex-col gap-4">
          {agents.explorer.output && (
            <div className="w-full p-4 rounded-md border border-[var(--color-explorer-start)]/30 bg-[var(--color-explorer-start)]/5 text-xs relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-[var(--color-explorer-start)]"></div>
              <h3 className="font-bold text-[var(--color-explorer-start)] mb-3 flex items-center gap-2">
                <span>📊</span> Dataset Profile (Auto-Detected)
              </h3>
              
              <div className="space-y-2 text-white/80">
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-white/50">Dataset:</span>
                  <span className="font-mono">{agents.explorer.output.name}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-white/50">Input Shape:</span>
                  <span className="font-mono">[{agents.explorer.output.input_shape?.join(', ')}]</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-white/50">Channels:</span>
                  <span className="font-mono">{agents.explorer.output.input_shape?.[0] === 1 ? '1 (Grayscale)' : agents.explorer.output.input_shape?.[0] === 3 ? '3 (RGB)' : agents.explorer.output.input_shape?.[0]}</span>
                </div>
                <div className="flex justify-between border-b border-white/5 pb-1">
                  <span className="text-white/50">Classes:</span>
                  <span className="font-mono">{agents.explorer.output.num_classes}</span>
                </div>
                
                <div className="pt-2 mt-2">
                  <span className="text-white/50 block mb-1">Recommended Architectures:</span>
                  <p className="text-[10px] text-white/70">{agents.explorer.output.recommended_architectures?.join(', ')}</p>
                </div>
              </div>
            </div>
          )}
          
          <div className="flex gap-3 w-full">
            {isRunning ? (
              <button 
                type="button"
                onClick={handleReset}
                className="flex-1 py-3 px-4 rounded-md font-bold text-sm bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30 transition-all"
              >
                STOP
              </button>
            ) : (
              <button 
                type="submit"
                className="flex-1 py-3 px-4 rounded-md font-bold text-sm text-white relative overflow-hidden group"
                style={{ background: 'linear-gradient(90deg, var(--color-architect-start), var(--color-architect-end))' }}
              >
                <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative flex items-center justify-center gap-2">
                  🚀 Launch Swarm
                </div>
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
