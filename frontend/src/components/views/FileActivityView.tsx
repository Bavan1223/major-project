import React, { useState } from 'react';
import { useSoc } from '../../context/SocContext';
import { FileActivityItem } from '../../types';
import {
  FolderOpen,
  FileCode,
  FileWarning,
  Lock,
  Search,
  Filter,
  KeyRound,
  ShieldCheck,
  AlertTriangle,
  Flame,
} from 'lucide-react';

export const FileActivityView: React.FC = () => {
  const { fileActivities, systemStatus, behavioralTelemetry } = useSoc();
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedOp, setSelectedOp] = useState<string>('ALL');

  const filtered = fileActivities.filter((item) => {
    if (selectedOp !== 'ALL' && item.operation !== selectedOp) return false;
    if (filterQuery.trim() !== '') {
      const q = filterQuery.toLowerCase();
      return (
        item.path.toLowerCase().includes(q) ||
        item.process.toLowerCase().includes(q) ||
        item.operation.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top 3 Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Card 1: Shannon Entropy Gauge */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <Lock className="w-4 h-4 text-[#adc6ff]" />
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
                Average Buffer Entropy
              </span>
            </div>
            <span
              className={`font-mono text-[9px] px-1.5 py-0.5 rounded border ${
                behavioralTelemetry.entropyAvg > 7.0
                  ? 'bg-[#93000a]/30 border-[#ffb4ab] text-[#ffb4ab] font-bold animate-pulse'
                  : 'bg-[#00a572]/20 border-[#4edea3]/30 text-[#4edea3]'
              }`}
            >
              {behavioralTelemetry.entropyAvg > 7.0 ? 'ENCRYPTED THRESHOLD' : 'NORMAL RANGE'}
            </span>
          </div>

          <div className="flex items-end justify-between mt-3">
            <div>
              <div
                className={`text-[28px] font-bold font-mono leading-none ${
                  behavioralTelemetry.entropyAvg > 7.0 ? 'text-[#ffb4ab]' : 'text-[#4edea3]'
                }`}
              >
                {behavioralTelemetry.entropyAvg.toFixed(2)}
                <span className="text-[14px] text-[#c2c6d6] font-normal"> / 8.00</span>
              </div>
              <div className="font-mono text-[10px] text-[#c2c6d6] mt-1">
                Threshold: &gt; 7.80 = AES/RSA payload
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Canary Traps */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <KeyRound className="w-4 h-4 text-[#ffb786]" />
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
                Honeytoken Canary Status
              </span>
            </div>
            <span className="font-mono text-[9px] bg-[#df7412]/20 border border-[#ffb786]/30 text-[#ffb786] px-1.5 py-0.5 rounded">
              12 ACTIVE TRAPS
            </span>
          </div>

          <div className="mt-3">
            <div className="text-[28px] font-bold font-mono text-[#e1e2ec] leading-none">
              {systemStatus.threatState === 'critical' ? (
                <span className="text-[#ffb4ab] flex items-center gap-2">
                  <Flame className="w-6 h-6 animate-pulse" /> 1 TRIGGERED
                </span>
              ) : (
                <span className="text-[#4edea3] flex items-center gap-2">
                  <ShieldCheck className="w-6 h-6" /> 0 TRIPPED
                </span>
              )}
            </div>
            <div className="font-mono text-[10px] text-[#c2c6d6] mt-1">
              Bait file: <code className="text-[#adc6ff]">passwords_backup.kdbx</code>
            </div>
          </div>
        </div>

        {/* Card 3: Mass File Renames */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <FileWarning className="w-4 h-4 text-[#adc6ff]" />
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider">
                Extension Rewrite Rate
              </span>
            </div>
            <span className="font-mono text-[9px] bg-[#10131a] border border-[#424754] text-[#c2c6d6] px-1.5 py-0.5 rounded">
              .enc / .locked
            </span>
          </div>

          <div className="mt-3">
            <div className="text-[28px] font-bold font-mono text-[#e1e2ec] leading-none">
              {behavioralTelemetry.filesRenamed}{' '}
              <span className="text-[12px] text-[#c2c6d6] font-normal">files / min</span>
            </div>
            <div className="font-mono text-[10px] text-[#c2c6d6] mt-1">
              Monitored extensions: .docx, .xlsx, .pdf, .sql, .kdbx
            </div>
          </div>
        </div>
      </div>

      {/* File Activity Log Table */}
      <div className="bg-[#1d2027] border border-[#424754] rounded flex-1 flex flex-col overflow-hidden">
        {/* Table Header & Search */}
        <div className="p-3 border-b border-[#424754] flex flex-wrap justify-between items-center bg-[#272a31]/50 gap-2">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-[#adc6ff]" />
            <span className="font-mono text-[11px] font-bold text-[#e1e2ec] tracking-wider uppercase">
              VFS &amp; INOTIFY FILE STREAM
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8c909f]" />
              <input
                type="text"
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                placeholder="Search paths, processes..."
                className="bg-[#10131a] border border-[#424754] rounded pl-8 pr-3 py-1 font-mono text-[11px] text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] w-64 placeholder-[#8c909f]"
              />
            </div>

            {/* Operation Filter Buttons */}
            <div className="flex gap-1">
              {['ALL', 'ENCRYPTED', 'RENAMED', 'MODIFIED', 'CREATED'].map((op) => (
                <button
                  key={op}
                  onClick={() => setSelectedOp(op)}
                  className={`px-2 py-1 rounded font-mono text-[9px] font-bold border ${
                    selectedOp === op
                      ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                      : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                  }`}
                >
                  {op}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table Body */}
        <div className="overflow-auto max-h-[520px]">
          <table className="w-full text-left font-mono text-[11px] border-collapse">
            <thead className="sticky top-0 bg-[#32353c] border-b border-[#424754] z-10 text-[#c2c6d6] text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th className="p-2.5 pl-4 w-28">TIME (UTC)</th>
                <th className="p-2.5 w-24">OPERATION</th>
                <th className="p-2.5">TARGET FILE PATH</th>
                <th className="p-2.5 w-32">PROCESS (PID)</th>
                <th className="p-2.5 w-24 text-right">ENTROPY</th>
                <th className="p-2.5 pr-4 w-28 text-right">THREAT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#424754]/30 text-[#e1e2ec]">
              {filtered.map((item) => {
                const isEnc = item.operation === 'ENCRYPTED' || item.threatLevel === 'critical';
                const isCanary = item.isHoneytoken;

                return (
                  <tr
                    key={item.id}
                    className={`hover:bg-[#272a31] transition-colors ${
                      isEnc
                        ? 'bg-[#93000a]/15 border-l-2 border-l-[#ffb4ab]'
                        : isCanary
                        ? 'bg-[#df7412]/15 border-l-2 border-l-[#ffb786]'
                        : ''
                    }`}
                  >
                    <td className="p-2.5 pl-4 text-[#c2c6d6]">{item.time}</td>
                    <td className="p-2.5">
                      <span
                        className={`inline-block px-2 py-0.5 border rounded text-[9px] font-bold ${
                          item.operation === 'ENCRYPTED'
                            ? 'bg-[#93000a]/30 border-[#ffb4ab] text-[#ffb4ab]'
                            : item.operation === 'RENAMED'
                            ? 'bg-[#df7412]/20 border-[#ffb786] text-[#ffb786]'
                            : 'bg-[#10131a] border-[#424754] text-[#c2c6d6]'
                        }`}
                      >
                        {item.operation}
                      </span>
                    </td>
                    <td className="p-2.5 font-mono break-all">
                      <span className={isEnc ? 'text-[#ffb4ab] font-bold' : isCanary ? 'text-[#ffb786]' : 'text-[#e1e2ec]'}>
                        {item.path}
                      </span>
                      {isCanary && (
                        <span className="ml-2 px-1.5 py-0.2 bg-[#df7412]/30 text-[#ffb786] text-[8px] font-bold rounded border border-[#ffb786]">
                          HONEYTOKEN
                        </span>
                      )}
                    </td>
                    <td className="p-2.5 text-[#adc6ff]">
                      {item.process} ({item.pid})
                    </td>
                    <td
                      className={`p-2.5 text-right font-bold ${
                        item.entropy > 7.8 ? 'text-[#ffb4ab]' : 'text-[#4edea3]'
                      }`}
                    >
                      {item.entropy.toFixed(2)}
                    </td>
                    <td className="p-2.5 pr-4 text-right">
                      {isEnc ? (
                        <span className="text-[#ffb4ab] font-bold text-[10px] animate-pulse">
                          CRITICAL
                        </span>
                      ) : (
                        <span className="text-[#4edea3] text-[10px]">NORMAL</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
