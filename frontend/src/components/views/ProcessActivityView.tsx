import React, { useState } from 'react';
import { useSoc } from '../../context/SocContext';
import { ProcessItem } from '../../types';
import {
  Terminal,
  Cpu,
  HardDrive,
  AlertTriangle,
  Search,
  Filter,
  ShieldAlert,
  X,
  FileCode,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export const ProcessActivityView: React.FC = () => {
  const {
    processes,
    selectedProcess,
    setSelectedProcess,
    killProcess,
    triggerContainment,
    systemStatus,
  } = useSoc();

  const [searchQuery, setSearchQuery] = useState('');
  const [showRawLogModal, setShowRawLogModal] = useState(false);

  const activeProcess = selectedProcess || processes[0];

  const filteredProcesses = processes.filter((p) => {
    if (searchQuery.trim() === '') return true;
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.pid.toString().includes(q) ||
      p.executablePath.toLowerCase().includes(q) ||
      p.user.toLowerCase().includes(q) ||
      p.status.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top Metrics Bar (4 columns) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Metric 1: Active Processes */}
        <div className="bg-[#1d2027] p-3.5 rounded border border-[#424754] relative overflow-hidden group">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-[#c2c6d6]" />
              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-widest">
                Active Processes
              </span>
            </div>
            <div className="w-6 h-6 rounded-full bg-[#10131a] border border-[#424754] flex items-center justify-center">
              <span className="font-mono text-[9px] font-bold text-[#adc6ff]">98</span>
            </div>
          </div>
          <div className="text-[24px] font-bold text-[#e1e2ec] font-mono">1,492</div>
          <div className="font-mono text-[11px] text-[#4edea3] mt-1 flex items-center gap-1">
            <span>↓ -12 from baseline</span>
          </div>
          <svg
            className="absolute bottom-0 left-0 w-full h-8 text-[#4edea3]/20"
            preserveAspectRatio="none"
            viewBox="0 0 100 20"
          >
            <path d="M0 20 L0 15 L20 12 L40 18 L60 8 L80 14 L100 5 L100 20 Z" fill="currentColor" />
            <path
              d="M0 15 L20 12 L40 18 L60 8 L80 14 L100 5"
              fill="none"
              stroke="#4edea3"
              strokeWidth="1"
            />
          </svg>
        </div>

        {/* Metric 2: Suspicious Activity */}
        <div className="bg-[#1d2027] p-3.5 rounded border border-[#424754] relative overflow-hidden group">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-[#ffb4ab]" />
              <span className="font-mono text-[10px] font-bold text-[#ffb4ab] uppercase tracking-widest">
                Suspicious Activity
              </span>
            </div>
            <div className="w-6 h-6 rounded-full bg-[#10131a] border border-[#ffb4ab]/50 flex items-center justify-center">
              <span className="font-mono text-[9px] font-bold text-[#ffb4ab]">94</span>
            </div>
          </div>
          <div className="text-[24px] font-bold text-[#e1e2ec] font-mono">3</div>
          <div className="font-mono text-[11px] text-[#ffb4ab] mt-1 flex items-center gap-1">
            <span>↑ +3 in last hour</span>
          </div>
        </div>

        {/* Metric 3: CPU Utilization */}
        <div className="bg-[#1d2027] p-3.5 rounded border border-[#424754] relative overflow-hidden group">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-[#c2c6d6]" />
              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-widest">
                CPU Utilization
              </span>
            </div>
          </div>
          <div className="flex items-end gap-2 mt-1">
            <div className="text-[24px] font-bold text-[#e1e2ec] font-mono">
              42<span className="text-[14px] text-[#c2c6d6]">%</span>
            </div>
            <div className="flex-1 h-2 bg-[#10131a] rounded-full overflow-hidden mb-2 border border-[#424754]/50">
              <div className="h-full bg-[#adc6ff] w-[42%]" />
            </div>
          </div>
        </div>

        {/* Metric 4: Memory Usage */}
        <div className="bg-[#1d2027] p-3.5 rounded border border-[#424754] relative overflow-hidden group">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5">
              <HardDrive className="w-4 h-4 text-[#c2c6d6]" />
              <span className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-widest">
                Memory Usage
              </span>
            </div>
          </div>
          <div className="flex items-end gap-2 mt-1">
            <div className="text-[24px] font-bold text-[#e1e2ec] font-mono">
              6.4<span className="text-[14px] text-[#c2c6d6]">GB</span>
            </div>
            <div className="flex-1 h-2 bg-[#10131a] rounded-full overflow-hidden mb-2 border border-[#424754]/50">
              <div className="h-full bg-[#ffb786] w-[78%]" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Split Layout: Table (flex 3) & Process Inspector (flex 1.5) */}
      <div className="flex flex-col lg:flex-row gap-3 flex-1 min-h-[480px]">
        {/* Process Table */}
        <div className="flex-[3] bg-[#1d2027] rounded flex flex-col overflow-hidden border border-[#424754] shadow-lg">
          <div className="p-3 bg-[#272a31]/60 border-b border-[#424754] flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-[#adc6ff]" />
              <span className="text-[16px] font-bold text-[#e1e2ec]">Process Execution Log</span>
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8c909f]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter by Name, PID..."
                  className="bg-[#10131a] text-[#e1e2ec] font-mono text-[11px] rounded border border-[#424754] pl-8 pr-3 py-1 w-60 focus:outline-none focus:border-[#adc6ff]"
                />
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-left border-collapse font-mono text-[11px]">
              <thead>
                <tr className="bg-[#191b23] border-b border-[#424754] text-[#c2c6d6] text-[10px] uppercase font-bold tracking-wider">
                  <th className="p-2.5 pl-4 w-16">PID</th>
                  <th className="p-2.5">Process Name</th>
                  <th className="p-2.5">Executable Path</th>
                  <th className="p-2.5">User</th>
                  <th className="p-2.5 w-28">Status</th>
                  <th className="p-2.5 pr-4 text-right">Create Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#424754]/30 text-[#e1e2ec]">
                {filteredProcesses.map((proc) => {
                  const isSelected = activeProcess?.pid === proc.pid;
                  const isSuspicious = proc.status === 'SUSPICIOUS';
                  const isAnomalous = proc.status === 'ANOMALOUS';
                  const isTerminated = proc.status === 'TERMINATED';

                  return (
                    <tr
                      key={proc.pid}
                      onClick={() => setSelectedProcess(proc)}
                      className={`hover:bg-[#32353c] transition-colors cursor-pointer ${
                        isSelected ? 'bg-[#32353c] ring-1 ring-[#adc6ff]' : ''
                      } ${isSuspicious ? 'bg-[#93000a]/15' : isAnomalous ? 'bg-[#df7412]/10' : ''}`}
                    >
                      <td className="p-2.5 pl-4 text-[#c2c6d6]">{proc.pid}</td>
                      <td
                        className={`p-2.5 font-bold ${
                          isSuspicious
                            ? 'text-[#ffb4ab]'
                            : isAnomalous
                            ? 'text-[#ffb786]'
                            : isTerminated
                            ? 'line-through text-[#8c909f]'
                            : 'text-[#adc6ff]'
                        }`}
                      >
                        {proc.name}
                      </td>
                      <td className="p-2.5 text-[#c2c6d6] truncate max-w-[220px]">
                        {proc.executablePath}
                      </td>
                      <td className="p-2.5 text-[#e1e2ec]">{proc.user}</td>
                      <td className="p-2.5">
                        {isSuspicious ? (
                          <span className="inline-flex items-center gap-1.5 text-[#ffb4ab] bg-[#93000a]/30 px-2 py-0.5 rounded border border-[#ffb4ab]/30 text-[9px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#ffb4ab] animate-pulse" />
                            SUSPICIOUS
                          </span>
                        ) : isAnomalous ? (
                          <span className="inline-flex items-center gap-1.5 text-[#ffb786] bg-[#df7412]/20 px-2 py-0.5 rounded border border-[#ffb786]/30 text-[9px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#ffb786]" />
                            ANOMALOUS
                          </span>
                        ) : isTerminated ? (
                          <span className="inline-flex items-center gap-1 text-[#8c909f] text-[9px] uppercase font-bold">
                            TERMINATED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-[#4edea3] text-[9px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />
                            NORMAL
                          </span>
                        )}
                      </td>
                      <td className="p-2.5 pr-4 text-right text-[#c2c6d6]">{proc.createTime}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Process Inspector Panel (Right side, flex 1.5) */}
        {activeProcess && (
          <div className="flex-[1.5] bg-[#1d2027] rounded border border-[#424754] shadow-xl flex flex-col min-w-[320px]">
            {/* Header */}
            <div className="p-3 bg-[#32353c] border-b border-[#424754] flex justify-between items-center relative overflow-hidden">
              <div className="absolute inset-0 bg-[#93000a]/10 pointer-events-none" />
              <div className="flex items-center gap-2 relative z-10">
                <Terminal className="w-4 h-4 text-[#ffb4ab]" />
                <span className="font-mono text-[10px] font-bold text-[#e1e2ec] tracking-widest uppercase">
                  Process Inspector
                </span>
              </div>
              <span className="font-mono text-[10px] text-[#c2c6d6] relative z-10">
                PID: {activeProcess.pid}
              </span>
            </div>

            <div className="p-3.5 flex-1 overflow-y-auto space-y-3 font-mono text-[11px]">
              {/* Process Name & Path */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h3
                    className={`text-[18px] font-bold ${
                      activeProcess.status === 'SUSPICIOUS'
                        ? 'text-[#ffb4ab]'
                        : activeProcess.status === 'ANOMALOUS'
                        ? 'text-[#ffb786]'
                        : 'text-[#e1e2ec]'
                    }`}
                  >
                    {activeProcess.name}
                  </h3>
                  <span className="text-[10px] text-[#c2c6d6]">PID: {activeProcess.pid}</span>
                </div>
                <div className="text-[10px] text-[#c2c6d6] truncate bg-[#10131a] p-1.5 rounded border border-[#424754]">
                  {activeProcess.executablePath}
                </div>
              </div>

              {/* Threat Score */}
              <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex items-center justify-between">
                <div className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase">
                  THREAT SCORE
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-[#272a31] rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        (activeProcess.threatScore || 0) > 70
                          ? 'bg-[#ffb4ab]'
                          : (activeProcess.threatScore || 0) > 40
                          ? 'bg-[#ffb786]'
                          : 'bg-[#4edea3]'
                      }`}
                      style={{ width: `${activeProcess.threatScore || 10}%` }}
                    />
                  </div>
                  <span
                    className={`font-bold text-[12px] ${
                      (activeProcess.threatScore || 0) > 70 ? 'text-[#ffb4ab]' : 'text-[#e1e2ec]'
                    }`}
                  >
                    {activeProcess.threatScore || 0}/100
                  </span>
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div className="bg-[#10131a] p-2.5 rounded border border-[#424754]">
                  <div className="text-[#8c909f] uppercase mb-0.5">PARENT PROCESS</div>
                  <div className="text-[#e1e2ec] font-bold truncate">
                    {activeProcess.parentProcess || 'None'}
                  </div>
                </div>
                <div className="bg-[#10131a] p-2.5 rounded border border-[#424754]">
                  <div className="text-[#8c909f] uppercase mb-0.5">USER CONTEXT</div>
                  <div className="text-[#e1e2ec] font-bold truncate">{activeProcess.user}</div>
                </div>
                <div className="bg-[#10131a] p-2.5 rounded border border-[#424754] col-span-2">
                  <div className="text-[#8c909f] uppercase mb-0.5">COMMAND LINE</div>
                  <div className="text-[#ffb4ab] text-[10px] break-all">
                    {activeProcess.commandLine || activeProcess.executablePath}
                  </div>
                </div>
              </div>

              {/* Behavior Timeline */}
              <div>
                <div className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase mb-2">
                  BEHAVIOR TIMELINE
                </div>
                <div className="relative border-l border-[#424754] ml-2 pl-4 space-y-3.5 py-1">
                  {activeProcess.timeline && activeProcess.timeline.length > 0 ? (
                    activeProcess.timeline.map((item, idx) => (
                      <div key={idx} className="relative">
                        <div
                          className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full ${
                            item.type === 'critical'
                              ? 'bg-[#ffb4ab] shadow-[0_0_8px_rgba(255,180,171,0.8)]'
                              : item.type === 'handle'
                              ? 'bg-[#10131a] border-2 border-[#ffb786]'
                              : 'bg-[#10131a] border-2 border-[#adc6ff]'
                          }`}
                        />
                        <div className="text-[10px] text-[#8c909f]">{item.time}</div>
                        <div
                          className={`text-[12px] font-sans ${
                            item.type === 'critical'
                              ? 'text-[#ffb4ab] font-bold'
                              : item.type === 'terminated'
                              ? 'text-[#8c909f] italic'
                              : 'text-[#e1e2ec]'
                          }`}
                        >
                          {item.description}
                        </div>
                        {item.matchedRule && (
                          <div className="text-[9px] text-[#ffb4ab]/80 font-mono mt-0.5">
                            {item.matchedRule}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-[#8c909f] text-[11px] italic">
                      Standard process execution without flagged behavioral anomalies.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Actions Bar */}
            <div className="p-3 bg-[#191b23] border-t border-[#424754] flex gap-2">
              <button
                onClick={triggerContainment}
                className="flex-1 bg-[#93000a] text-[#ffdad6] font-mono text-[10px] font-bold py-2 rounded shadow hover:bg-[#ffb4ab] hover:text-[#690005] transition-colors flex justify-center items-center gap-1"
              >
                <Lock className="w-3.5 h-3.5" /> ISOLATE HOST
              </button>
              {activeProcess.status !== 'TERMINATED' && (
                <button
                  onClick={() => killProcess(activeProcess.pid)}
                  className="px-3 bg-[#272a31] text-[#ffb4ab] border border-[#ffb4ab]/40 font-mono text-[10px] font-bold py-2 rounded hover:bg-[#93000a]/30 transition-colors"
                >
                  KILL PID
                </button>
              )}
              <button
                onClick={() => setShowRawLogModal(true)}
                className="px-3 bg-[#10131a] text-[#c2c6d6] font-mono text-[10px] rounded border border-[#424754] hover:bg-[#272a31]"
              >
                RAW LOG
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Raw Log Modal */}
      {showRawLogModal && activeProcess && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-[#191b23] border border-[#424754] rounded-lg max-w-2xl w-full p-5 shadow-2xl space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-[#424754] pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-[#adc6ff]" />
                <h3 className="text-[15px] font-bold text-[#e1e2ec]">
                  Raw Audit Log // PID {activeProcess.pid}
                </h3>
              </div>
              <button
                onClick={() => setShowRawLogModal(false)}
                className="text-[#8c909f] hover:text-[#e1e2ec]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <pre className="bg-[#0b0e15] text-[#4edea3] p-4 rounded border border-[#424754] text-[11px] overflow-auto max-h-80 leading-relaxed">
              {JSON.stringify(
                {
                  timestamp: new Date().toISOString(),
                  audit_id: `AUD-${activeProcess.pid}-${Date.now()}`,
                  process: {
                    pid: activeProcess.pid,
                    name: activeProcess.name,
                    path: activeProcess.executablePath,
                    user: activeProcess.user,
                    command: activeProcess.commandLine,
                    threatScore: activeProcess.threatScore,
                  },
                  eBPF_hooks: {
                    sys_enter_write: 'HOOK_ENABLED',
                    sys_enter_openat: 'HOOK_ENABLED',
                    vfs_unlink: 'FLAGGED',
                  },
                  entropy_analysis: {
                    sampled_blocks: 128,
                    max_shannon_entropy: 7.96,
                    verdict: activeProcess.threatScore ? 'SUSPICIOUS_ENCRYPTOR' : 'NORMAL',
                  },
                },
                null,
                2
              )}
            </pre>

            <div className="flex justify-end">
              <button
                onClick={() => setShowRawLogModal(false)}
                className="px-4 py-1.5 bg-[#272a31] text-[#e1e2ec] text-[11px] rounded hover:bg-[#32353c]"
              >
                Close Log
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
