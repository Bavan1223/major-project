import React, { useState } from 'react';
import { useSoc } from '../../context/SocContext';
import { NetworkConnection } from '../../types';
import {
  Network,
  Search,
  Filter,
  ArrowUpDown,
  Globe,
  Repeat,
  Terminal,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';

export const NetworkActivityView: React.FC = () => {
  const { connections, setSelectedProcess, processes, setActiveTab } = useSoc();
  const [filterText, setFilterText] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('ALL');
  const [selectedConnection, setSelectedConnection] = useState<NetworkConnection | null>(null);

  const filteredConnections = connections.filter((conn) => {
    if (selectedStatusFilter !== 'ALL' && conn.indicator !== selectedStatusFilter) return false;
    if (filterText.trim() !== '') {
      const q = filterText.toLowerCase();
      return (
        conn.process.toLowerCase().includes(q) ||
        conn.localAddress.toLowerCase().includes(q) ||
        conn.remoteAddress.toLowerCase().includes(q) ||
        conn.pid.toString().includes(q) ||
        conn.status.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Top 3 Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Card 1: Established Connections */}
        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden group">
          <div className="absolute right-0 top-0 w-32 h-32 bg-[#adc6ff]/5 rounded-full blur-2xl -mr-16 -mt-16 transition-all group-hover:bg-[#adc6ff]/10" />
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <ArrowUpDown className="w-4 h-4 text-[#adc6ff]" />
              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                ESTABLISHED CONNECTIONS
              </span>
            </div>
            <div className="flex items-center justify-center w-6 h-6 rounded-full border border-[#adc6ff]/30">
              <span className="font-mono text-[8px] text-[#adc6ff] font-bold">98%</span>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">1,248</span>
            <span className="font-mono text-[11px] text-[#4edea3] mb-0.5">↑ 12/s</span>
          </div>
          <div className="mt-4 h-1.5 w-full bg-[#272a31] rounded-full overflow-hidden">
            <div className="h-full bg-[#adc6ff] w-3/4 rounded-full" />
          </div>
        </div>

        {/* Card 2: Unique Remote IPs */}
        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden group">
          <div className="absolute right-0 top-0 w-32 h-32 bg-[#4edea3]/5 rounded-full blur-2xl -mr-16 -mt-16 transition-all group-hover:bg-[#4edea3]/10" />
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <Globe className="w-4 h-4 text-[#4edea3]" />
              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                UNIQUE REMOTE IPs
              </span>
            </div>
            <div className="flex items-center justify-center w-6 h-6 rounded-full border border-[#4edea3]/30">
              <span className="font-mono text-[8px] text-[#4edea3] font-bold">92%</span>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">342</span>
            <span className="font-mono text-[11px] text-[#c2c6d6] mb-0.5">Last 5 min</span>
          </div>
          <div className="mt-4 flex gap-1 h-7 items-end">
            <div className="w-full bg-[#4edea3]/20 h-[20%] rounded-xs" />
            <div className="w-full bg-[#4edea3]/40 h-[40%] rounded-xs" />
            <div className="w-full bg-[#4edea3]/30 h-[30%] rounded-xs" />
            <div className="w-full bg-[#4edea3]/60 h-[60%] rounded-xs" />
            <div className="w-full bg-[#4edea3]/80 h-[80%] rounded-xs" />
            <div className="w-full bg-[#4edea3] h-full rounded-xs" />
            <div className="w-full bg-[#4edea3]/70 h-[70%] rounded-xs" />
            <div className="w-full bg-[#4edea3]/50 h-[50%] rounded-xs" />
          </div>
        </div>

        {/* Card 3: Repeated Connections */}
        <div className="bg-[#1d2027] rounded p-4 border border-[#424754] relative overflow-hidden group">
          <div className="absolute right-0 top-0 w-32 h-32 bg-[#ffb4ab]/5 rounded-full blur-2xl -mr-16 -mt-16 transition-all group-hover:bg-[#ffb4ab]/10" />
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-1.5 text-[#c2c6d6]">
              <Repeat className="w-4 h-4 text-[#ffb4ab]" />
              <span className="font-mono text-[10px] font-bold tracking-wider uppercase">
                REPEATED CONNECTIONS
              </span>
            </div>
            <div className="flex items-center justify-center w-6 h-6 rounded-full border border-[#ffb4ab]/30 bg-[#93000a]/20">
              <span className="font-mono text-[8px] text-[#ffb4ab] font-bold">45%</span>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-[26px] font-bold text-[#e1e2ec] font-mono leading-none">86</span>
            <span className="font-mono text-[11px] text-[#ffb4ab] mb-0.5">Threshold Exceeded</span>
          </div>
          <div className="mt-4 relative h-7 w-full">
            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 20">
              <path
                className="text-[#ffb4ab]/20"
                d="M0,15 Q10,5 20,10 T40,15 T60,5 T80,18 T100,8 L100,20 L0,20 Z"
                fill="currentColor"
              />
              <path
                className="text-[#ffb4ab]"
                d="M0,15 Q10,5 20,10 T40,15 T60,5 T80,18 T100,8"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="bg-[#1d2027] rounded border border-[#424754] flex flex-col flex-1 overflow-hidden">
        {/* Search & Filter Header */}
        <div className="p-3 border-b border-[#424754] flex flex-wrap justify-between items-center bg-[#272a31]/50 gap-2">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-[#adc6ff]" />
            <span className="font-mono text-[11px] font-bold text-[#e1e2ec] tracking-wider uppercase">
              LIVE NETWORK CONNECTIONS
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8c909f]" />
              <input
                type="text"
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                placeholder="Filter by IP, Port, Process..."
                className="bg-[#10131a] border border-[#424754] rounded pl-8 pr-3 py-1 font-mono text-[11px] text-[#e1e2ec] focus:outline-none focus:border-[#adc6ff] w-64 placeholder-[#8c909f]"
              />
            </div>

            {/* Quick Status Filter */}
            <div className="flex gap-1">
              {['ALL', 'SUSPICIOUS', 'ANOMALY', 'NORMAL'].map((st) => (
                <button
                  key={st}
                  onClick={() => setSelectedStatusFilter(st)}
                  className={`px-2 py-1 rounded font-mono text-[9px] font-bold border ${
                    selectedStatusFilter === st
                      ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                      : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Connections Table */}
        <div className="overflow-auto max-h-[540px]">
          <table className="w-full text-left border-collapse font-mono text-[11px]">
            <thead className="sticky top-0 bg-[#32353c] border-b border-[#424754] z-10 text-[#c2c6d6] text-[10px] uppercase font-bold tracking-wider">
              <tr>
                <th className="p-2.5 pl-4 whitespace-nowrap w-24">TIME (UTC)</th>
                <th className="p-2.5 whitespace-nowrap">PROCESS</th>
                <th className="p-2.5 whitespace-nowrap w-20">PID</th>
                <th className="p-2.5 whitespace-nowrap">LOCAL ADDRESS</th>
                <th className="p-2.5 whitespace-nowrap">REMOTE ADDRESS</th>
                <th className="p-2.5 whitespace-nowrap w-24">STATUS</th>
                <th className="p-2.5 pr-4 whitespace-nowrap w-32 text-right">INDICATOR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#424754]/30 text-[#e1e2ec]">
              {filteredConnections.map((conn) => {
                const isSuspicious = conn.indicator === 'SUSPICIOUS';
                const isAnomaly = conn.indicator === 'ANOMALY';

                return (
                  <tr
                    key={conn.id}
                    onClick={() => setSelectedConnection(conn)}
                    className={`hover:bg-[#272a31] transition-colors group cursor-pointer ${
                      isSuspicious
                        ? 'bg-[#93000a]/15 border-l-2 border-l-[#ffb4ab]'
                        : isAnomaly
                        ? 'bg-[#ffb786]/10'
                        : ''
                    }`}
                  >
                    <td className="p-2.5 pl-4 text-[#c2c6d6]">{conn.time}</td>
                    <td className="p-2.5 flex items-center gap-2">
                      {isSuspicious ? (
                        <AlertTriangle className="w-3.5 h-3.5 text-[#ffb4ab] animate-pulse" />
                      ) : (
                        <Terminal className="w-3.5 h-3.5 text-[#8c909f]" />
                      )}
                      <span className={isSuspicious ? 'text-[#ffb4ab] font-bold' : isAnomaly ? 'text-[#ffb786]' : 'text-[#adc6ff]'}>
                        {conn.process}
                      </span>
                    </td>
                    <td className="p-2.5 text-[#c2c6d6]">{conn.pid}</td>
                    <td className="p-2.5 text-[#e1e2ec]">{conn.localAddress}</td>
                    <td className="p-2.5 font-bold text-[#e1e2ec]">{conn.remoteAddress}</td>
                    <td className="p-2.5">
                      {conn.status === 'ESTAB' ? (
                        <span className="text-[#4edea3] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />
                          ESTAB
                        </span>
                      ) : conn.status === 'SYN_SENT' ? (
                        <span className="text-[#ffb4ab] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#ffb4ab] animate-ping" />
                          SYN_SENT
                        </span>
                      ) : conn.status === 'LISTEN' ? (
                        <span className="text-[#adc6ff] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#adc6ff]" />
                          LISTEN
                        </span>
                      ) : (
                        <span className="text-[#c2c6d6] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#8c909f]" />
                          {conn.status}
                        </span>
                      )}
                    </td>
                    <td className="p-2.5 pr-4 text-right">
                      {isSuspicious ? (
                        <span className="inline-block px-2 py-0.5 border border-[#ffb4ab] bg-[#93000a]/40 rounded text-[#ffb4ab] font-bold animate-pulse text-[9px]">
                          SUSPICIOUS
                        </span>
                      ) : isAnomaly ? (
                        <span className="inline-block px-2 py-0.5 border border-[#ffb786]/50 bg-[#df7412]/20 rounded text-[#ffb786] font-bold text-[9px]">
                          ANOMALY
                        </span>
                      ) : (
                        <span className="inline-block px-2 py-0.5 border border-[#424754] rounded text-[#c2c6d6] bg-[#10131a] text-[9px]">
                          NORMAL
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Connection Detail Drawer / Dialog */}
      {selectedConnection && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-[#191b23] border border-[#424754] rounded-lg max-w-md w-full p-5 shadow-2xl space-y-4 font-mono text-[11px]">
            <div className="flex items-center justify-between border-b border-[#424754] pb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-[#adc6ff]" />
                <h3 className="text-[15px] font-bold text-[#e1e2ec]">Socket Inspection</h3>
              </div>
              <button
                onClick={() => setSelectedConnection(null)}
                className="text-[#8c909f] hover:text-[#e1e2ec]"
              >
                ✕
              </button>
            </div>

            <div className="bg-[#10131a] p-3 rounded border border-[#424754] space-y-2">
              <div className="flex justify-between">
                <span className="text-[#8c909f]">Target Process:</span>
                <span className="text-[#adc6ff] font-bold">{selectedConnection.process} (PID {selectedConnection.pid})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8c909f]">Local Socket:</span>
                <span className="text-[#e1e2ec]">{selectedConnection.localAddress}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8c909f]">Remote Peer:</span>
                <span className="text-[#ffb786] font-bold">{selectedConnection.remoteAddress}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8c909f]">Connection State:</span>
                <span className="text-[#4edea3]">{selectedConnection.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8c909f]">Heuristic Risk:</span>
                <span className={selectedConnection.indicator === 'SUSPICIOUS' ? 'text-[#ffb4ab] font-bold' : 'text-[#4edea3]'}>
                  {selectedConnection.indicator}
                </span>
              </div>
            </div>

            <div className="pt-2 border-t border-[#424754] flex gap-2">
              <button
                onClick={() => {
                  const proc = processes.find((p) => p.pid === selectedConnection.pid);
                  if (proc) {
                    setSelectedProcess(proc);
                    setActiveTab('process-activity');
                  }
                  setSelectedConnection(null);
                }}
                className="flex-1 bg-[#adc6ff] text-[#002e6a] font-bold py-2 rounded flex items-center justify-center gap-1.5 hover:bg-[#d8e2ff]"
              >
                Inspect Process <ExternalLink className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setSelectedConnection(null)}
                className="px-4 bg-[#272a31] text-[#e1e2ec] rounded hover:bg-[#32353c]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
