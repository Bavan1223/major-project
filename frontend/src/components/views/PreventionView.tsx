import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  Shield,
  ShieldAlert,
  Lock,
  Unlock,
  RotateCcw,
  FileCheck,
  Zap,
  Network,
  Terminal,
  CheckCircle,
  AlertTriangle,
  Clock,
  Activity,
} from 'lucide-react';

export const PreventionView: React.FC = () => {
  const {
    systemStatus,
    activeIncident,
    incidents,
    auditLog,
    actionLogs,
    protectLabFiles,
    isolateProcess,
    isolateNetwork,
    createSnapshot,
    restoreLabFiles,
    simulateAttack,
    acknowledgeIncident,
    containIncident,
    resolveIncident,
    closeIncident,
  } = useSoc();

  const hasActive = !!activeIncident;
  const incidentId = activeIncident?.incident_id || '';
  const incidentStatus = activeIncident?.status || 'NONE';

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">

      {/* Top: Prevention Status Banner */}
      <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-[#00a572]/20 border border-[#4edea3]/40 flex items-center justify-center text-[#4edea3]">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider">
              PREVENTION & RECOVERY CENTER
            </div>
            <div className="text-[15px] font-bold text-[#e1e2ec]">
              Protection Mode: <span className="text-[#4edea3]">DRY_RUN</span> | Safe Lab: <span className="text-[#4edea3]">ENABLED</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-[#8c909f] bg-[#10131a] px-2 py-1 rounded border border-[#424754]">
            Active Incident: {hasActive ? `${incidentId} (${incidentStatus})` : 'NONE'}
          </span>
        </div>
      </div>

      {/* Incident Lifecycle Controls */}
      {hasActive && (
        <div className="bg-[#1d2027] border border-[#ffb786]/40 rounded p-4">
          <div className="font-mono text-[10px] font-bold text-[#ffb786] uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> INCIDENT LIFECYCLE — {incidentId}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => acknowledgeIncident(incidentId)}
              disabled={incidentStatus !== 'OPEN'}
              className="px-3 py-2 bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold rounded hover:bg-[#32353c] disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5" /> ACKNOWLEDGE
            </button>
            <button
              onClick={() => containIncident(incidentId)}
              disabled={incidentStatus === 'CONTAINED' || incidentStatus === 'RESOLVED' || incidentStatus === 'CLOSED'}
              className="px-3 py-2 bg-[#93000a]/40 border border-[#ffb4ab]/40 text-[#ffb4ab] font-mono text-[11px] font-bold rounded hover:bg-[#93000a]/60 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Lock className="w-3.5 h-3.5" /> CONTAIN
            </button>
            <button
              onClick={() => resolveIncident(incidentId)}
              disabled={incidentStatus === 'RESOLVED' || incidentStatus === 'CLOSED'}
              className="px-3 py-2 bg-[#00a572]/20 border border-[#4edea3]/40 text-[#4edea3] font-mono text-[11px] font-bold rounded hover:bg-[#00a572]/40 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <CheckCircle className="w-3.5 h-3.5" /> RESOLVE
            </button>
            <button
              onClick={() => closeIncident(incidentId)}
              disabled={incidentStatus === 'CLOSED'}
              className="px-3 py-2 bg-[#272a31] border border-[#424754] text-[#c2c6d6] font-mono text-[11px] font-bold rounded hover:bg-[#32353c] disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Unlock className="w-3.5 h-3.5" /> CLOSE
            </button>
          </div>
          <div className="mt-2 font-mono text-[10px] text-[#8c909f]">
            Status: {incidentStatus} | Risk: {activeIncident?.risk_level} | Signals: {activeIncident?.signals.join(', ') || 'none'}
          </div>
        </div>
      )}

      {/* Prevention Actions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">

        {/* Protect Lab Files */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#4edea3] mb-2">
              <FileCheck className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">FILE PROTECTION</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Protect Lab Files</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Create a backup snapshot of ~/ransomware-lab/test-files for recovery purposes.
            </p>
          </div>
          <button
            onClick={protectLabFiles}
            className="mt-3 w-full bg-[#272a31] border border-[#424754] hover:bg-[#4edea3]/20 hover:border-[#4edea3] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            PROTECT FILES
          </button>
        </div>

        {/* Process Isolation */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#adc6ff] mb-2">
              <Terminal className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">PROCESS ISOLATION</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Isolate Suspect Process</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Simulate process isolation for the detected suspect process. No actual kill (DRY_RUN).
            </p>
          </div>
          <button
            onClick={() => isolateProcess(activeIncident?.pid || undefined, activeIncident?.process || undefined)}
            className="mt-3 w-full bg-[#272a31] border border-[#424754] hover:bg-[#adc6ff]/20 hover:border-[#adc6ff] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            ISOLATE PROCESS
          </button>
        </div>

        {/* Network Isolation */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#ffb786] mb-2">
              <Network className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">NETWORK ISOLATION</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Simulate Network Isolation</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Record a network isolation recommendation. No firewall rules modified (DRY_RUN).
            </p>
          </div>
          <button
            onClick={isolateNetwork}
            className="mt-3 w-full bg-[#272a31] border border-[#424754] hover:bg-[#ffb786]/20 hover:border-[#ffb786] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            SIMULATE ISOLATION
          </button>
        </div>

        {/* Recovery Snapshot */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#4edea3] mb-2">
              <RotateCcw className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">RECOVERY SNAPSHOT</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Create Recovery Snapshot</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Snapshot the current state of test-files for potential rollback.
            </p>
          </div>
          <button
            onClick={createSnapshot}
            className="mt-3 w-full bg-[#272a31] border border-[#424754] hover:bg-[#4edea3]/20 hover:border-[#4edea3] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            CREATE SNAPSHOT
          </button>
        </div>

        {/* Restore Lab Files */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#adc6ff] mb-2">
              <RotateCcw className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">FILE RESTORATION</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Restore Lab Files</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Restore test-files from the latest recovery snapshot.
            </p>
          </div>
          <button
            onClick={restoreLabFiles}
            className="mt-3 w-full bg-[#272a31] border border-[#424754] hover:bg-[#adc6ff]/20 hover:border-[#adc6ff] text-[#e1e2ec] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            RESTORE FILES
          </button>
        </div>

        {/* Run Simulation */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[#ffb4ab] mb-2">
              <Zap className="w-4 h-4" />
              <span className="font-mono text-[10px] font-bold uppercase">SAFE SIMULATION</span>
            </div>
            <h3 className="text-[14px] font-bold text-[#e1e2ec]">Run Safe Ransomware Simulation</h3>
            <p className="text-[11px] text-[#c2c6d6] mt-1">
              Execute simulator/safe_simulator.py to generate ransomware-like behavior for detection testing.
            </p>
          </div>
          <button
            onClick={simulateAttack}
            className="mt-3 w-full bg-[#272a31] border border-[#ffb4ab]/30 hover:bg-[#ffb4ab]/20 hover:border-[#ffb4ab] text-[#ffb4ab] font-mono text-[11px] font-bold py-2 rounded transition-colors"
          >
            RUN SIMULATION
          </button>
        </div>
      </div>

      {/* Incident History + Audit Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">

        {/* Incident History */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 max-h-60 overflow-y-auto">
          <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider mb-2">
            INCIDENT HISTORY ({incidents.length})
          </div>
          {incidents.length === 0 ? (
            <div className="text-[11px] text-[#8c909f] font-mono">No incidents recorded.</div>
          ) : (
            <div className="space-y-1.5">
              {incidents.slice(0, 10).map((inc) => (
                <div key={inc.incident_id} className="flex items-center justify-between bg-[#10131a] rounded p-2 border border-[#424754]">
                  <div>
                    <span className="font-mono text-[10px] text-[#e1e2ec] font-bold">{inc.incident_id}</span>
                    <span className="font-mono text-[9px] text-[#8c909f] ml-2">{inc.risk_level}</span>
                  </div>
                  <span className={`font-mono text-[9px] px-1.5 py-0.5 rounded ${
                    inc.status === 'OPEN' ? 'bg-[#ffb4ab]/20 text-[#ffb4ab]' :
                    inc.status === 'INVESTIGATING' ? 'bg-[#ffb786]/20 text-[#ffb786]' :
                    inc.status === 'CONTAINED' ? 'bg-[#adc6ff]/20 text-[#adc6ff]' :
                    inc.status === 'RESOLVED' ? 'bg-[#4edea3]/20 text-[#4edea3]' :
                    'bg-[#424754] text-[#8c909f]'
                  }`}>
                    {inc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Audit Log */}
        <div className="bg-[#0b0e15] border border-[#424754] rounded p-4 max-h-60 overflow-y-auto">
          <div className="font-mono text-[10px] font-bold text-[#8c909f] uppercase tracking-wider border-b border-[#424754]/50 pb-1 mb-2">
            AUDIT LOG ({auditLog.length})
          </div>
          {auditLog.length === 0 ? (
            <div className="text-[11px] text-[#8c909f] font-mono">No audit entries.</div>
          ) : (
            <div className="space-y-1 font-mono text-[10px]">
              {auditLog.slice(0, 20).map((entry, idx) => (
                <div key={idx} className={`flex items-start gap-2 ${entry.success ? 'text-[#c2c6d6]' : 'text-[#ffb4ab]'}`}>
                  <Clock className="w-3 h-3 mt-0.5 shrink-0 text-[#8c909f]" />
                  <div>
                    <span className="text-[#8c909f]">{entry.timestamp?.substring(11, 19) || '--'}</span>
                    {' '}
                    <span className="font-bold">{entry.action}</span>
                    {' — '}
                    <span>{entry.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action Log */}
      <div className="bg-[#0b0e15] border border-[#424754] rounded p-3 font-mono text-[11px] space-y-1 overflow-y-auto max-h-32">
        <div className="text-[#8c909f] text-[9px] uppercase font-bold border-b border-[#424754]/50 pb-1 mb-1">
          SESSION ACTION LOG
        </div>
        {actionLogs.length === 0 && <div className="text-[#8c909f]">No actions this session.</div>}
        {actionLogs.map((log, idx) => (
          <div key={idx} className={
            log.includes('CONTAINMENT') || log.includes('CONTAIN') ? 'text-[#4edea3] font-bold' :
            log.includes('ERROR') ? 'text-[#ffb4ab]' : 'text-[#c2c6d6]'
          }>{log}</div>
        ))}
      </div>
    </div>
  );
};
