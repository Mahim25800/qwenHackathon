"use client";

import React from 'react';
import { ControlPanel } from '../components/ControlPanel';
import { AgentTopology } from '../components/AgentTopology';
import { DebateTimeline } from '../components/DebateTimeline';
import { CodeViewer } from '../components/CodeViewer';
import { ResultsPanel } from '../components/ResultsPanel';
import { useAppStore } from '../lib/store';

export default function Home() {
  const { error } = useAppStore();

  return (
    <div className="flex flex-col h-screen overflow-hidden p-4 gap-4 relative">
      {/* Background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--color-explorer-start)] blur-[120px] opacity-10 mix-blend-screen"></div>
        <div className="absolute top-[40%] right-[-10%] w-[40%] h-[60%] rounded-full bg-[var(--color-architect-end)] blur-[150px] opacity-10 mix-blend-screen"></div>
        <div className="absolute bottom-[-20%] left-[20%] w-[60%] h-[40%] rounded-full bg-[var(--color-critic-start)] blur-[120px] opacity-10 mix-blend-screen"></div>
      </div>

      {/* Header */}
      <header className="flex items-center justify-between glass-panel px-6 py-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-architect-start)] to-[var(--color-architect-end)] flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(139,92,246,0.5)]">
            N
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            Neural<span className="text-white/50">Swarm</span>
          </h1>
        </div>
        <div className="text-xs text-white/40 font-mono tracking-wider uppercase border border-white/10 px-3 py-1 rounded-full bg-black/20">
          Multi-Agent Cognitive Architecture
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 gap-4 overflow-hidden min-h-0">
        {/* Left Column - Control Panel */}
        <div className="w-[300px] shrink-0">
          <ControlPanel />
        </div>

        {/* Center Column - Topology & Code */}
        <div className="flex flex-col flex-1 gap-4 min-w-0 relative">
          <div className="glass-panel h-[60%] overflow-hidden relative">
            <div className="absolute top-4 left-4 z-10 text-xs font-bold text-white/50 tracking-wider uppercase">
              Agent Topology
            </div>
            <AgentTopology />
          </div>
          <div className="h-[40%]">
            <CodeViewer />
          </div>
          <ResultsPanel />
        </div>

        {/* Right Column - Debate Log */}
        <div className="w-[350px] shrink-0">
          <DebateTimeline />
        </div>
      </div>

      {/* Error Toast */}
      {error && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 bg-red-500/20 text-red-400 px-6 py-3 rounded-lg border border-red-500/30 shadow-[0_0_20px_rgba(239,68,68,0.2)] z-50 backdrop-blur-md flex items-center gap-3">
          <span className="font-bold">Error:</span> {error}
        </div>
      )}
    </div>
  );
}
