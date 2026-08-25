import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  ShieldCheck,
  Lock,
  Unlock,
  Radio,
  Server,
  Terminal,
  RotateCcw,
  Flame,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
} from 'lucide-react';

export const ResponseView: React.FC = () => {
  const {
    systemStatus,
    toggleSafeLabMode,
    triggerContainment,
    restoreHost,
    actionLogs,
    processes,
    killProcess,
  } = useSoc();

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top Banner: Safe Lab Mode and Host Isolation Status */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
        {/* Safe Lab Mode (Dry Run) Card */}
        <div className="md:col-span-6 bg-[#1d2027] border border-[#424754] rounded p-4 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider">
                SAFETY CONTROLLER
              </span>
              <span
                className={`font-mono text-[9px] px-2 py-0.5 rounded border font-bold ${
                  systemStatus.safeLabMode
                    ? 'bg-[#00a572]/20 border-[#4edea3]/40 text-[#4edea3]'
                    : 'bg-[#93000a]/20 border-[#ffb4ab]/40 text-[#ffb4ab]'
                }`}
              >
                {systemStatus.safeLabMode ? 'DRY-RUN SAFE' : 'LIVE ARMAMENT'}
              </span>
            </div>
            <div className="text-[16px] font-bold text-[#e1e2ec] mt-1">Safe Lab Mode</div>
            <div className="text-[12px] text-[#c2c6d6] max-w-sm mt-0.5">
              When enabled, network drops and process kills are simulated in isolation memory without severing host SSH/management pipes.
            </div>
          </div>

          <button
            onClick={toggleSafeLabMode}
            className={`px-4 py-2 rounded font-mono text-[11px] font-bold border transition-colors ${
              systemStatus.safeLabMode
                ? 'bg-[#00a572] text-[#002e6a] border-[#4edea3]'
                : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
            }`}
          >
            {systemStatus.safeLabMode ? 'SAFE LAB: ON' : 'SAFE LAB: OFF'}
          </button>
        </div>

        {/* Host Isolation Status */}
        <div
          className={`md:col-span-6 border rounded p-4 flex justify-between items-center ${
            systemStatus.hostIsolated
              ? 'bg-[#93000a]/15 border-[#ffb4ab]'
              : 'bg-[#1d2027] border-[#424754]'
          }`}
        >
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                NETWORK INTERFACE // eno1
              </span>
              {systemStatus.hostIsolated ? (
                <span className="bg-[#93000a] text-[#ffdad6] text-[9px] font-mono px-2 py-0.5 rounded border border-[#ffb4ab] font-bold animate-pulse">
                  ISOLATED
                </span>
              ) : (
                <span className="bg-[#00a572]/20 text-[#4edea3] text-[9px] font-mono px-2 py-0.5 rounded border border-[#4edea3]/30 font-bold">
                  CONNECTED
                </span>
              )}
            </div>
            <div className="text-[16px] font-bold text-[#e1e2ec] mt-1">Host Network Quarantine</div>
            <div className="text-[12px] text-[#c2c6d6] max-w-sm mt-0.5">
              {systemStatus.hostIsolated
                ? 'All ingress/egress dropped via iptables rules except SOC control channel (port 443/3000).'
                : 'Host interface is operating with unrestricted LAN/WAN routing.'}
            </div>
          </div>

          {systemStatus.hostIsolated ? (
            <button
              onClick={restoreHost}
              className="px-4 py-2 bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold rounded hover:bg-[#32353c] flex items-center gap-1.5"
            >
              <Unlock className="w-3.5 h-3.5" /> RE-ENABLE HOST
            </button>
          ) : (
            <button
              onClick={triggerContainment}
              className="px-4 py-2 bg-[#93000a] border border-[#ffb4ab] text-[#ffdad6] font-mono text-[11px] font-bold rounded hover:bg-[#ffb4ab] hover:text-[#690005] transition-colors flex items-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5" /> ISOLATE NOW
            </button>
          )}
        </div>
      </div>

      {/* Response Action Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Playbook 1: Automated Remediation */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#adc6ff] mb-1">
              <Terminal className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">Automated Playbook #1</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Process Tree Execution Halt</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Inspects parent-child lineage and sends SIGKILL to all untrusted binaries with threat score &gt; 75.
            </p>
          </div>
          <button
            onClick={() => {
              processes.forEach((p) => {
                if ((p.threatScore || 0) > 50) killProcess(p.pid);
              });
            }}
            className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#ffb4ab]/20 hover:border-[#ffb4ab] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            EXECUTE PROCESS PURGE
          </button>
        </div>

        {/* Playbook 2: VSS Rollback */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#4edea3] mb-1">
              <RotateCcw className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">Automated Playbook #2</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Shadow Copy Snapshot Restore</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Validates immutable storage snapshot at 14:20:00 UTC and mounts clean restore points for modified folders.
            </p>
          </div>
          <button
            onClick={triggerContainment}
            className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#4edea3]/20 hover:border-[#4edea3] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            RESTORE CLEAN SNAPSHOT
          </button>
        </div>

        {/* Playbook 3: Canary Trap Re-arming */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#ffb786] mb-1">
              <FileCheck className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">Automated Playbook #3</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Honeytoken Fleet Re-Arm</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Deploys 12 high-attraction decoy credential databases and document lures with kernel inotify tripwires.
            </p>
          </div>
          <button className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#ffb786]/20 hover:border-[#ffb786] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors">
            RE-DEPLOY 12 DECOYS
          </button>
        </div>
      </div>

      {/* Real-Time Action Audit Log */}
      <div className="bg-[#0b0e15] border border-[#424754] rounded p-4 flex-1 flex flex-col min-h-[220px]">
        <div className="font-mono text-[10px] font-bold text-[#8c909f] uppercase tracking-wider border-b border-[#424754] pb-2 mb-2 flex justify-between">
          <span>CONTAINMENT &amp; REMEDIATION AUDIT LOG</span>
          <span>REAL-TIME KERNEL EVENTS</span>
        </div>
        <div className="space-y-1.5 font-mono text-[11px] overflow-y-auto flex-1 max-h-56">
          {actionLogs.map((log, idx) => (
            <div
              key={idx}
              className={
                log.includes('CONTAINMENT') || log.includes('RESTORE')
                  ? 'text-[#4edea3] font-semibold'
                  : log.includes('KILL') || log.includes('ISOLATED')
                  ? 'text-[#ffb4ab]'
                  : 'text-[#c2c6d6]'
              }
            >
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
