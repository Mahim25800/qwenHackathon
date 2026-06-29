import React, { useState, useEffect } from 'react';
import { useAppStore } from '../lib/store';
import { MetricsCard } from './MetricsCard';

export function ResultsPanel() {
  const { finalResult, currentIteration, swarmState, swarmConfig, currentCode } = useAppStore();
  const [isTraining, setIsTraining] = useState(false);
  const [trainLogs, setTrainLogs] = useState<any[]>([]);
  const [trainStatus, setTrainStatus] = useState<string>('');

  if (swarmState !== 'completed' || !finalResult) {
    return null;
  }

  // Check if finalResult is approved by checking the backend's official final_status
  const isApproved = finalResult.final_status === 'approved';
  
  // Use the actual parameter count from the Critic's evaluation if available
  const paramCount = finalResult.final_critique?.param_count || finalResult.final_blueprint?.total_params || finalResult.param_count || finalResult.total_params || 0;
  let macCount = finalResult.final_blueprint?.total_macs || finalResult.mac_count || finalResult.total_macs || 0;
  
  // Fallback MAC calculation if backend didn't provide one (approx 185x params for simple CNNs)
  if (macCount === 0 && paramCount > 0) {
    macCount = paramCount * 185;
  }

  const budgetRatio = paramCount > 0 ? ((paramCount / swarmConfig.max_params) * 100).toFixed(1) : "0";
  const reason = finalResult.reason || (isApproved ? 'Final architecture accepted.' : 'Max iterations reached without consensus.');
  const title = isApproved ? 'Swarm Consensus Reached' : 'Debate Terminated';

  const handleTestTrain = async () => {
    if (!currentCode) return;
    setIsTraining(true);
    setTrainLogs([]);
    setTrainStatus('Initializing...');
    
    // Convert shape string "3,32,32" to array [3,32,32]
    const inputShape = swarmConfig.input_shape.split(',').map(s => parseInt(s.trim(), 10));

    try {
      const response = await fetch('http://localhost:8000/api/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pytorch_code: currentCode,
          input_shape: inputShape,
          num_classes: swarmConfig.num_classes
        })
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6));
            setTrainLogs(prev => [...prev, data]);
            setTrainStatus(data.message || `Training Epoch ${data.epoch}...`);
            if (data.status === 'completed' || data.status === 'error') {
              break;
            }
          }
        }
      }
    } catch (e) {
      setTrainStatus('Error starting training');
    }
  };

  return (
    <div className="glass-panel p-6 border-t-2 border-green-500/30 animate-slide-up bg-[#0a0a0f]/95 backdrop-blur-3xl absolute top-4 left-4 right-4 rounded-xl shadow-2xl z-50 overflow-hidden max-h-[80vh] flex flex-col">
      <div className="flex justify-between items-start mb-6 shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <span className={`w-3 h-3 rounded-full ${isApproved ? 'bg-green-400' : 'bg-amber-400'} animate-pulse-glow`}></span>
            {title}
          </h2>
          <p className="text-white/60 text-sm mt-1">
            {reason}
          </p>
        </div>
        
        <div className="flex flex-col items-end gap-2">
          <div className={`px-4 py-2 rounded-lg font-bold border ${
            isApproved ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
          }`}>
            {isApproved ? 'ARCHITECTURE APPROVED' : 'MAX ITERATIONS REACHED'}
          </div>
          {isApproved && !isTraining && (
            <button 
              onClick={handleTestTrain}
              className="bg-blue-500/20 hover:bg-blue-500/40 text-blue-300 border border-blue-500/30 px-3 py-1.5 rounded-md text-xs font-bold transition-colors"
            >
              ▶ Test Train Model (Dummy Data)
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 shrink-0 mb-4">
        <MetricsCard 
          label="Total Parameters" 
          value={!isApproved && paramCount > 0 ? `${(paramCount / 1000000).toFixed(2)} / ${(swarmConfig.max_params / 1000000).toFixed(2)}` : (paramCount / 1000000).toFixed(2)} 
          unit={`M (${budgetRatio}%)`}
          color="var(--color-architect-end)"
        />
        <MetricsCard 
          label="Compute (MACs)" 
          value={(macCount / 1000000).toFixed(2)} 
          unit="M"
          color="var(--color-critic-end)"
        />
        <MetricsCard 
          label="Iterations" 
          value={currentIteration}
          color="var(--color-explorer-start)"
        />
        <MetricsCard 
          label="Status" 
          value={isApproved ? "Optimal" : "Sub-optimal"}
          color={isApproved ? "rgba(0,255,100,0.8)" : "rgba(255,150,0,0.8)"}
        />
      </div>

      {isTraining && (
        <div className="mt-4 border-t border-white/10 pt-4 overflow-y-auto custom-scrollbar flex-1 min-h-[200px]">
          <h3 className="text-sm font-bold text-white/80 mb-2">Live Training Terminal (5 Epochs)</h3>
          <div className="bg-black/60 rounded p-4 font-mono text-xs text-green-400/80 h-full overflow-y-auto">
            {trainLogs.map((log, i) => (
              <div key={i} className="mb-1">
                <span className="text-white/40">[{new Date().toISOString().split('T')[1].split('.')[0]}]</span>{' '}
                {log.status === 'training' ? (
                  <span>Epoch {log.epoch}/5 - Loss: <span className="text-yellow-400">{log.loss.toFixed(4)}</span> - Acc: <span className="text-blue-400">{log.accuracy.toFixed(2)}%</span></span>
                ) : log.status === 'error' ? (
                  <span className="text-red-400 font-bold">ERROR: {log.message}</span>
                ) : (
                  <span className="text-blue-300">{log.message}</span>
                )}
              </div>
            ))}
            {trainStatus && !trainStatus.includes('Training Epoch') && !trainStatus.includes('completed') && !trainStatus.includes('Error') && (
              <div className="animate-pulse text-white/50">{trainStatus}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
