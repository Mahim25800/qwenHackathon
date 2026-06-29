import React, { useEffect } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/themes/prism-tomorrow.css'; // You can install this or add custom styles
import { useAppStore } from '../lib/store';

export function CodeViewer() {
  const { currentCode, currentIteration } = useAppStore();

  useEffect(() => {
    Prism.highlightAll();
  }, [currentCode]);

  return (
    <div className="glass-panel h-full flex flex-col overflow-hidden relative group">
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none"></div>
      
      <div className="flex justify-between items-center p-3 border-b border-white/10 bg-black/20 z-10">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-bold text-white/90">PyTorch Implementation</h2>
          {currentIteration > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-white/10 text-[10px] text-white/70 border border-white/5">
              Iteration {currentIteration}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => {
              const element = document.createElement("a");
              const file = new Blob([currentCode], {type: 'text/plain'});
              element.href = URL.createObjectURL(file);
              element.download = "generated_model.py";
              document.body.appendChild(element);
              element.click();
              document.body.removeChild(element);
            }}
            disabled={!currentCode}
            className="text-xs font-bold text-[var(--color-architect-start)] hover:text-white bg-[var(--color-architect-start)]/10 hover:bg-[var(--color-architect-start)]/30 px-3 py-1 rounded transition-colors border border-[var(--color-architect-start)]/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ↓ Download .py
          </button>
          <button 
            onClick={() => navigator.clipboard.writeText(currentCode)}
            disabled={!currentCode}
            className="text-xs text-white/50 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-1 rounded transition-colors border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Copy Code
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-0 bg-[#0d0d12] max-h-[400px]">
        {currentCode ? (
          <pre className="m-0 p-4 text-xs font-mono !bg-transparent">
            <code className="language-python">
              {currentCode}
            </code>
          </pre>
        ) : (
          <div className="h-full flex items-center justify-center text-white/20 text-sm italic font-mono">
            # No architecture generated yet
          </div>
        )}
      </div>
    </div>
  );
}
