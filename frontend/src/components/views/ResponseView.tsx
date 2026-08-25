import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  ShieldCheck,
  Lock,
  Unlock,
  Terminal,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Shield,
  Activity,
} from 'lucide-react';

export const ResponseView: React.FC = () => {
  const {
    systemStatus,
    activeIncident,
    toggleSafeLabMode,
    triggerContainment,
    restoreHost,
    actionLogs,
    protectLabFiles,
    isolateProcess,
    createSnapshot,
    restoreLabFiles,
  } = useSoc();

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top Banner: Safe Lab Mode and Host Isolation Status */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
        {/* Safe Lab Mode Card */}
        <div className="md:col-span-6 bg-[#1d2027] border border-[#424754] rounded p-4 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider">
                SAFETY CONTROLLER
              </span>
              <span className={`font-mono text-[9px] px-2 py-0.5 rounded border font-bold ${
                systemStatus.safeLabMode
                  ? 'bg-[#00a572]/20 border-[#4edea3]/40 text-[#4edea3]'
                  : 'bg-[#93000a]/20 border-[#ffb4ab]/40 text-[#ffb4ab]'
              }`}>
                {systemStatus.safeLabMode ? 'DRY-RUN SAFE' : 'LIVE'}
              </span>
            </div>
            <div className="text-[16px] font-bold text-[#e1e2ec] mt-1">Safe Lab Mode</div>
            <div className="text-[12px] text-[#c2c6d6] max-w-sm mt-0.5">
              All containment actions are simulated. No destructive operations are performed on the system.
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
        <div className={`md:col-span-6 border rounded p-4 flex justify-between items-center ${
          systemStatus.hostIsolated ? 'bg-[#93000a]/15 border-[#ffb4ab]' : 'bg-[#1d2027] border-[#424754]'
        }`}>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider">
                CONTAINMENT STATUS
              </span>
              {systemStatus.hostIsolated ? (
                <span className="bg-[#93000a] text-[#ffdad6] text-[9px] font-mono px-2 py-0.5 rounded border border-[#ffb4ab] font-bold">
                  CONTAINED
                </span>
              ) : (
                <span className="bg-[#00a572]/20 text-[#4edea3] text-[9px] font-mono px-2 py-0.5 rounded border border-[#4edea3]/30 font-bold">
                  NOT CONTAINED
                </span>
              )}
            </div>
            <div className="text-[16px] font-bold text-[#e1e2ec] mt-1">Safe Containment</div>
            <div className="text-[12px] text-[#c2c6d6] max-w-sm mt-0.5">
              {systemStatus.hostIsolated
                ? 'Containment active (DRY_RUN). Files protected, process/network isolation simulated.'
                : 'No active containment. System operating normally.'}
            </div>
          </div>
          {systemStatus.hostIsolated ? (
            <button
              onClick={restoreHost}
              className="px-4 py-2 bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold rounded hover:bg-[#32353c] flex items-center gap-1.5"
            >
              <Unlock className="w-3.5 h-3.5" /> RESTORE
            </button>
          ) : (
            <button
              onClick={triggerContainment}
              className="px-4 py-2 bg-[#93000a] border border-[#ffb4ab] text-[#ffdad6] font-mono text-[11px] font-bold rounded hover:bg-[#ffb4ab] hover:text-[#690005] transition-colors flex items-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5" /> CONTAIN (DRY-RUN)
            </button>
          )}
        </div>
      </div>

      {/* Active Incident Info */}
      {activeIncident && (
        <div className="bg-[#1d2027] border border-[#ffb786]/40 rounded p-4">
          <div className="font-mono text-[10px] font-bold text-[#ffb786] uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> ACTIVE INCIDENT
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[11px]">
            <div>
              <div className="text-[#8c909f]">ID</div>
              <div className="text-[#e1e2ec] font-bold">{activeIncident.incident_id}</div>
            </div>
            <div>
              <div className="text-[#8c909f]">Status</div>
              <div className="text-[#ffb786] font-bold">{activeIncident.status}</div>
            </div>
            <div>
              <div className="text-[#8c909f]">Risk Level</div>
              <div className="text-[#ffb4ab] font-bold">{activeIncident.risk_level}</div>
            </div>
            <div>
              <div className="text-[#8c909f]">Response</div>
              <div className="text-[#e1e2ec] font-bold">{activeIncident.response_action}</div>
            </div>
          </div>
        </div>
      )}

      {/* Response Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#adc6ff] mb-1">
              <Terminal className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">PROCESS RESPONSE</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Isolate Suspect Process</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Simulate isolation of the attributed suspect process (DRY_RUN — no actual process kill).
            </p>
          </div>
          <button
            onClick={() => isolateProcess(activeIncident?.pid || undefined, activeIncident?.process || undefined)}
            className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#adc6ff]/20 hover:border-[#adc6ff] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            ISOLATE PROCESS (DRY-RUN)
          </button>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#4edea3] mb-1">
              <RotateCcw className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">RECOVERY</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Restore Lab Files</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Restore test-files from the latest recovery snapshot to recover from simulated attack.
            </p>
          </div>
          <button
            onClick={restoreLabFiles}
            className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#4edea3]/20 hover:border-[#4edea3] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            RESTORE FROM SNAPSHOT
          </button>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#ffb786] mb-1">
              <FileCheck className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">PROTECTION</span>
            </div>
            <h3 className="text-[15px] font-bold text-[#e1e2ec]">Protect Lab Files</h3>
            <p className="text-[12px] text-[#c2c6d6] mt-1">
              Create a protective backup of the controlled test environment before further action.
            </p>
          </div>
          <button
            onClick={protectLabFiles}
            className="w-full bg-[#272a31] border border-[#424754] hover:bg-[#ffb786]/20 hover:border-[#ffb786] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            BACKUP LAB FILES
          </button>
        </div>
      </div>

      {/* Action Audit Log */}
      <div className="bg-[#0b0e15] border border-[#424754] rounded p-4 flex-1 flex flex-col min-h-[180px]">
        <div className="font-mono text-[10px] font-bold text-[#8c909f] uppercase tracking-wider border-b border-[#424754] pb-2 mb-2">
          RESPONSE & CONTAINMENT AUDIT LOG (DRY-RUN)
        </div>
        <div className="space-y-1.5 font-mono text-[11px] overflow-y-auto flex-1 max-h-48">
          {actionLogs.length === 0 && (
            <div className="text-[#8c909f]">No actions recorded this session.</div>
          )}
          {actionLogs.map((log, idx) => (
            <div
              key={idx}
              className={
                log.includes('CONTAIN') || log.includes('RESTORE') ? 'text-[#4edea3] font-semibold' :
                log.includes('ERROR') || log.includes('ISOLAT') ? 'text-[#ffb4ab]' :
                'text-[#c2c6d6]'
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
