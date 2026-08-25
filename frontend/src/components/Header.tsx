import React, { useState } from 'react';
import { useSoc } from '../context/SocContext';
import { Shield, User, Bell, Flame, RotateCcw, AlertTriangle, ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  const { systemStatus, currentTimeString, simulateAttack, resetSimulation } = useSoc();
  const [showSimMenu, setShowSimMenu] = useState(false);

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-[#1d2027]/90 backdrop-blur-md border-b border-[#424754] z-40 flex items-center justify-between px-4 select-none">
      {/* Protected Host Details */}
      <div className="flex items-center gap-4 border-r border-[#424754] pr-6">
        <div className="w-9 h-9 rounded bg-[#10131a] border border-[#424754] flex items-center justify-center text-[#adc6ff]">
          <Shield className="w-5 h-5 text-[#adc6ff]" />
        </div>
        <div>
          <div className="font-mono text-[10px] font-bold text-[#e1e2ec] tracking-widest uppercase">
            RANSOMWARE DEFENSE // REAL-TIME SOC
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6] flex items-center gap-1.5">
            Protected Host:{' '}
            <span className="text-[#adc6ff] font-semibold">Ubuntu Linux (192.168.74.131)</span>
            {systemStatus.hostIsolated && (
              <span className="ml-2 px-1.5 py-0.2 bg-[#93000a] text-[#ffdad6] text-[9px] font-bold rounded border border-[#ffb4ab]">
                ISOLATED
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Action Controls & Real-Time Indicators */}
      <div className="flex items-center gap-5">
        {/* Attack Simulation Controller */}
        <div className="relative">
          <button
            onClick={() => setShowSimMenu(!showSimMenu)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded border text-[11px] font-mono transition-colors ${
              systemStatus.threatState === 'critical'
                ? 'bg-[#93000a]/30 border-[#ffb4ab] text-[#ffb4ab] hover:bg-[#93000a]/50'
                : 'bg-[#191b23] border-[#424754] text-[#c2c6d6] hover:bg-[#272a31] hover:text-[#e1e2ec]'
            }`}
          >
            {systemStatus.threatState === 'critical' ? (
              <>
                <Flame className="w-3.5 h-3.5 text-[#ffb4ab] animate-pulse" />
                <span>THREAT DETECTED</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-3.5 h-3.5 text-[#4edea3]" />
                <span>STATE: NORMAL</span>
              </>
            )}
          </button>

          {showSimMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-[#191b23] border border-[#424754] rounded shadow-2xl p-2 z-50 font-mono text-[11px]">
              <div className="text-[10px] text-[#8c909f] uppercase px-2 py-1 border-b border-[#424754]">
                SOC State Simulator
              </div>
              <button
                onClick={() => {
                  simulateAttack();
                  setShowSimMenu(false);
                }}
                className="w-full text-left px-2 py-2 mt-1 rounded hover:bg-[#93000a]/30 text-[#ffb4ab] flex items-center gap-2"
              >
                <Flame className="w-3.5 h-3.5" />
                <span>Detonate Ransomware Test</span>
              </button>
              <button
                onClick={() => {
                  resetSimulation();
                  setShowSimMenu(false);
                }}
                className="w-full text-left px-2 py-2 rounded hover:bg-[#00a572]/20 text-[#4edea3] flex items-center gap-2"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset to Baseline Normal</span>
              </button>
            </div>
          )}
        </div>

        {/* Live Monitoring Badge */}
        <div className="flex items-center gap-2 px-3 py-1 bg-[#272a31] rounded border border-[#424754]">
          <span className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse" />
          <span className="font-mono text-[11px] text-[#4edea3] font-semibold tracking-wide">
            LIVE MONITORING
          </span>
        </div>

        {/* UTC Time & Sync Indicator */}
        <div className="flex flex-col items-end">
          <div className="font-mono text-[13px] font-semibold text-[#e1e2ec]">
            {currentTimeString}
          </div>
          <div className="font-mono text-[9px] text-[#c2c6d6] tracking-wider uppercase">
            API ONLINE // SYSTEM SYNCED
          </div>
        </div>

        {/* User Profile Avatar */}
        <div className="w-8 h-8 rounded-full bg-[#adc6ff] flex items-center justify-center text-[#002e6a] shadow-inner font-bold cursor-pointer hover:opacity-90">
          <User className="w-4 h-4" />
        </div>
      </div>
    </header>
  );
};
