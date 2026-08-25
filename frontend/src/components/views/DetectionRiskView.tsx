import React, { useState } from 'react';
import { useSoc } from '../../context/SocContext';
import {
  AlertTriangle,
  ShieldAlert,
  Lock,
  Activity,
  Flame,
  CheckCircle,
  FileWarning,
  Trash2,
  KeyRound,
  Check,
  RotateCcw,
  Zap,
} from 'lucide-react';

export const DetectionRiskView: React.FC = () => {
  const {
    systemStatus,
    triggerContainment,
    restoreHost,
    actionLogs,
    simulateAttack,
    resetSimulation,
  } = useSoc();

  const [containmentSuccess, setContainmentSuccess] = useState(false);
  const [selectedPlanItems, setSelectedPlanItems] = useState({
    isolate: true,
    killTree: true,
    restoreShadow: true,
    quarantine: true,
  });

  const handleAuthorize = () => {
    triggerContainment();
    setContainmentSuccess(true);
  };

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top Banner / Incident Header */}
      <div className="bg-[#93000a]/20 border border-[#ffb4ab] rounded p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="flex items-center gap-4 z-10">
          <div className="w-12 h-12 rounded bg-[#ffb4ab]/20 border border-[#ffb4ab] flex items-center justify-center text-[#ffb4ab] shrink-0">
            <AlertTriangle className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="bg-[#93000a] text-[#ffdad6] text-[10px] font-mono font-bold px-2 py-0.5 rounded border border-[#ffb4ab]/40">
                CRITICAL SEVERITY
              </span>
              <span className="text-[#adc6ff] text-[10px] font-mono bg-[#191b23] px-2 py-0.5 rounded border border-[#424754]">
                HOST: 192.168.74.131
              </span>
              <span className="text-[#ffb786] text-[10px] font-mono bg-[#191b23] px-2 py-0.5 rounded border border-[#424754]">
                INC-2023-891A
              </span>
              {systemStatus.hostIsolated && (
                <span className="text-[#4edea3] text-[10px] font-mono bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/40 flex items-center gap-1 font-bold">
                  <CheckCircle className="w-3 h-3" /> THREAT CONTAINED
                </span>
              )}
            </div>
            <h1 className="text-[20px] font-bold text-[#ffb4ab] tracking-tight">
              INC-2023-891A: ACTIVE ENCRYPTION &amp; SHADOW COPY DELETION
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 z-10">
          {systemStatus.hostIsolated ? (
            <button
              onClick={restoreHost}
              className="bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold px-4 py-2 rounded hover:bg-[#32353c] flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" /> RESTORE HOST STATE
            </button>
          ) : (
            <button
              onClick={handleAuthorize}
              className="bg-[#ffb4ab] text-[#690005] font-mono text-[12px] font-bold px-5 py-2.5 rounded shadow-lg hover:bg-white transition-all flex items-center gap-2 animate-pulse"
            >
              <Lock className="w-4 h-4" /> AUTHORIZE CONTAINMENT
            </button>
          )}
        </div>

        {/* Glow */}
        <div className="absolute right-0 top-0 w-96 h-96 bg-[#ffb4ab]/5 blur-3xl pointer-events-none" />
      </div>

      {/* Narrative & High Level Analysis */}
      <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-widest flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" /> BEHAVIORAL ANALYSIS NARRATIVE
          </div>
          <span className="font-mono text-[10px] text-[#c2c6d6]">
            Algorithm: Random Forest + AST Graph Anomaly
          </span>
        </div>
        <p className="text-[13px] text-[#e1e2ec] leading-relaxed">
          At 14:22:15 UTC, process <span className="text-[#ffb4ab] font-mono font-bold">PID 8934 (vssadmin.exe)</span> executed a shadow copy wipe command (<code className="text-[#ffb786] bg-[#10131a] px-1 py-0.5 rounded">Delete Shadows /All /Quiet</code>). Concurrently, <span className="text-[#ffb4ab] font-mono font-bold">PID 8842 (svchost.exe masquerading)</span> initiated rapid file overwrites across <code className="text-[#adc6ff] bg-[#10131a] px-1 py-0.5 rounded">C:\Users\Admin\Documents\</code> with file extensions rewritten to <code className="text-[#ffb786]">.enc</code>. Average payload entropy rose from baseline 3.2 to <strong>7.94</strong> (Shannon Entropy threshold &gt; 7.8 indicates strong symmetric encryption cipher like AES-256).
        </p>
      </div>

      {/* Middle 2 Columns: Signals & Timeline Graph vs ML Assessment & Containment */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* Left 7 cols: 3 Detection Signals & Entropy Graph */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          {/* 3 Triggered Signals */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-3.5 space-y-2.5">
            <div className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase tracking-wider mb-2">
              TRIGGERED HEURISTIC SIGNALS (3)
            </div>

            {/* Signal 1 */}
            <div className="bg-[#10131a] border border-[#ffb4ab]/50 rounded p-3 flex items-start gap-3">
              <div className="w-7 h-7 rounded bg-[#93000a]/40 border border-[#ffb4ab] flex items-center justify-center text-[#ffb4ab] shrink-0 mt-0.5">
                <FileWarning className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[13px] text-[#ffb4ab]">
                    High-Entropy Mass Encryption
                  </span>
                  <span className="font-mono text-[10px] text-[#ffb4ab] bg-[#93000a]/30 px-1.5 py-0.5 rounded border border-[#ffb4ab]/30">
                    CRITICAL
                  </span>
                </div>
                <div className="text-[11px] text-[#c2c6d6] mt-0.5 font-mono">
                  18 files modified in 3.1s | Average Entropy: 7.94 / 8.00 (AES/ChaCha signature)
                </div>
              </div>
            </div>

            {/* Signal 2 */}
            <div className="bg-[#10131a] border border-[#ffb4ab]/50 rounded p-3 flex items-start gap-3">
              <div className="w-7 h-7 rounded bg-[#93000a]/40 border border-[#ffb4ab] flex items-center justify-center text-[#ffb4ab] shrink-0 mt-0.5">
                <Trash2 className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[13px] text-[#ffb4ab]">
                    Volume Shadow Copy Deletion (Inhibited Recovery)
                  </span>
                  <span className="font-mono text-[10px] text-[#ffb4ab] bg-[#93000a]/30 px-1.5 py-0.5 rounded border border-[#ffb4ab]/30">
                    MITRE T1490
                  </span>
                </div>
                <div className="text-[11px] text-[#c2c6d6] mt-0.5 font-mono">
                  vssadmin.exe Delete Shadows /All /Quiet executed via hidden cmd.exe instance
                </div>
              </div>
            </div>

            {/* Signal 3 */}
            <div className="bg-[#10131a] border border-[#ffb786]/50 rounded p-3 flex items-start gap-3">
              <div className="w-7 h-7 rounded bg-[#df7412]/30 border border-[#ffb786] flex items-center justify-center text-[#ffb786] shrink-0 mt-0.5">
                <KeyRound className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[13px] text-[#ffb786]">
                    Honeytoken Decoy Canary Tripped
                  </span>
                  <span className="font-mono text-[10px] text-[#ffb786] bg-[#df7412]/20 px-1.5 py-0.5 rounded border border-[#ffb786]/30">
                    CANARY #4
                  </span>
                </div>
                <div className="text-[11px] text-[#c2c6d6] mt-0.5 font-mono">
                  Access detected on bait vault: C:\vault\passwords_backup.kdbx
                </div>
              </div>
            </div>
          </div>

          {/* Entropy Spike Chart */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-3.5 flex flex-col">
            <div className="flex items-center justify-between mb-2">
              <div className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                SHANNON ENTROPY TRAJECTORY (THRESHOLD = 7.80)
              </div>
              <span className="font-mono text-[10px] text-[#ffb4ab] font-bold">PEAK: 7.95</span>
            </div>

            <div className="w-full h-32 relative bg-[#10131a] rounded border border-[#424754] p-2 flex items-center">
              {/* Threshold line */}
              <div className="absolute left-0 right-0 top-[26%] border-b border-dashed border-[#ffb4ab]/60 z-0">
                <span className="absolute right-2 -top-3 text-[9px] font-mono text-[#ffb4ab]">
                  7.80 ENCRYPTION THRESHOLD
                </span>
              </div>

              {/* Entropy SVG Graph */}
              <svg className="w-full h-full relative z-10" preserveAspectRatio="none" viewBox="0 0 300 100">
                {/* Fill under graph */}
                <path
                  d="M 0 85 L 40 82 L 80 84 L 120 80 L 160 78 L 190 75 L 210 30 L 230 18 L 260 16 L 300 15 L 300 100 L 0 100 Z"
                  fill="url(#entropyGrad)"
                />
                {/* Stroke */}
                <path
                  d="M 0 85 L 40 82 L 80 84 L 120 80 L 160 78 L 190 75 L 210 30 L 230 18 L 260 16 L 300 15"
                  fill="none"
                  stroke="#ffb4ab"
                  strokeWidth="2.5"
                />
                <defs>
                  <linearGradient id="entropyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ffb4ab" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#ffb4ab" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div className="flex justify-between font-mono text-[9px] text-[#8c909f] mt-1.5">
              <span>T-60s (Baseline 3.20)</span>
              <span>T-30s</span>
              <span>T-15s (Spike start)</span>
              <span className="text-[#ffb4ab] font-bold">Now (7.94 Critical)</span>
            </div>
          </div>
        </div>

        {/* Right 5 cols: ML Confidence & Response Playbook */}
        <div className="lg:col-span-5 flex flex-col gap-3">
          {/* ML Assessment Card */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-[#424754] pb-2">
              <span className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase">
                ML CLASSIFIER ASSESSMENT
              </span>
              <span className="font-mono text-[9px] text-[#4edea3] bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/30">
                HIGH CONFIDENCE
              </span>
            </div>

            <div className="flex items-center justify-around my-3">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-[#272a31] stroke-current"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeWidth="3.5"
                  />
                  <path
                    className="text-[#ffb4ab] stroke-current transition-all duration-1000"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeDasharray="99.64, 100"
                    strokeLinecap="round"
                    strokeWidth="3.5"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="font-mono text-[18px] font-bold text-[#ffb4ab] leading-none">
                    99.64%
                  </span>
                  <span className="font-mono text-[8px] text-[#c2c6d6] uppercase mt-0.5">
                    LIKELIHOOD
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 font-mono text-[10px]">
                <div className="text-[#8c909f]">Family: <span className="text-[#e1e2ec] font-bold">LockBit / BlackCat Variant</span></div>
                <div className="text-[#8c909f]">Target: <span className="text-[#e1e2ec]">User Documents</span></div>
                <div className="text-[#8c909f]">False Positive: <span className="text-[#4edea3]">&lt; 0.001%</span></div>
              </div>
            </div>
          </div>

          {/* Containment Execution Plan */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col flex-1">
            <div className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase tracking-wider mb-3">
              RECOMMENDED CONTAINMENT ACTION
            </div>

            <div className="space-y-2 flex-1 font-mono text-[11px]">
              <label className="flex items-center gap-2 p-2 bg-[#10131a] rounded border border-[#424754] cursor-pointer hover:bg-[#272a31]">
                <input
                  type="checkbox"
                  checked={selectedPlanItems.isolate}
                  onChange={(e) => setSelectedPlanItems({ ...selectedPlanItems, isolate: e.target.checked })}
                  className="rounded accent-[#adc6ff]"
                />
                <span className="text-[#e1e2ec]">1. Network Quarantine (Block all ports except SOC)</span>
              </label>

              <label className="flex items-center gap-2 p-2 bg-[#10131a] rounded border border-[#424754] cursor-pointer hover:bg-[#272a31]">
                <input
                  type="checkbox"
                  checked={selectedPlanItems.killTree}
                  onChange={(e) => setSelectedPlanItems({ ...selectedPlanItems, killTree: e.target.checked })}
                  className="rounded accent-[#adc6ff]"
                />
                <span className="text-[#e1e2ec]">2. Terminate Process Tree (PID 8842, 8934)</span>
              </label>

              <label className="flex items-center gap-2 p-2 bg-[#10131a] rounded border border-[#424754] cursor-pointer hover:bg-[#272a31]">
                <input
                  type="checkbox"
                  checked={selectedPlanItems.restoreShadow}
                  onChange={(e) => setSelectedPlanItems({ ...selectedPlanItems, restoreShadow: e.target.checked })}
                  className="rounded accent-[#adc6ff]"
                />
                <span className="text-[#e1e2ec]">3. Restore Snapshot from 14:20:00 UTC</span>
              </label>
            </div>

            <button
              onClick={handleAuthorize}
              disabled={systemStatus.hostIsolated}
              className={`w-full mt-4 font-mono text-[12px] font-bold py-2.5 rounded shadow flex items-center justify-center gap-2 transition-all ${
                systemStatus.hostIsolated
                  ? 'bg-[#00a572]/20 border border-[#4edea3] text-[#4edea3] cursor-default'
                  : 'bg-[#ffb4ab] text-[#690005] hover:bg-white'
              }`}
            >
              {systemStatus.hostIsolated ? (
                <>
                  <Check className="w-4 h-4" /> CONTAINMENT EXECUTED
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" /> EXECUTE CONTAINMENT SEQUENCE
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Action Log Terminal */}
      <div className="bg-[#0b0e15] border border-[#424754] rounded p-3 font-mono text-[11px] space-y-1 overflow-y-auto max-h-36">
        <div className="text-[#8c909f] text-[9px] uppercase font-bold border-b border-[#424754]/50 pb-1 mb-1">
          Real-Time Audit Log &amp; Automated Responses
        </div>
        {actionLogs.map((log, idx) => (
          <div
            key={idx}
            className={
              log.includes('CONTAINMENT') || log.includes('PROCESS KILL')
                ? 'text-[#4edea3] font-bold'
                : log.includes('CRITICAL') || log.includes('RANSOMWARE')
                ? 'text-[#ffb4ab]'
                : 'text-[#c2c6d6]'
            }
          >
            {log}
          </div>
        ))}
      </div>
    </div>
  );
};
