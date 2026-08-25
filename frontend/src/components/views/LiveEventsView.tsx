import React, { useState } from 'react';
import { useSoc } from '../../context/SocContext';
import { SocEvent, SeverityType, SourceType } from '../../types';
import {
  Zap,
  Filter,
  Pause,
  Play,
  Search,
  CheckCircle2,
  AlertOctagon,
  ChevronDown,
  Info,
  X,
  ExternalLink,
} from 'lucide-react';

export const LiveEventsView: React.FC = () => {
  const {
    events,
    systemStatus,
    toggleStream,
    clearEvents,
    setSelectedProcess,
    processes,
    setActiveTab,
  } = useSoc();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<SeverityType | 'ALL'>('ALL');
  const [selectedSource, setSelectedSource] = useState<SourceType | 'ALL'>('ALL');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [inspectEvent, setInspectEvent] = useState<SocEvent | null>(null);

  const filteredEvents = events.filter((e) => {
    if (selectedSeverity !== 'ALL' && e.sev !== selectedSeverity) return false;
    if (selectedSource !== 'ALL' && e.source !== selectedSource) return false;
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      return (
        e.process.toLowerCase().includes(q) ||
        e.event.toLowerCase().includes(q) ||
        e.indicator.toLowerCase().includes(q) ||
        e.source.toLowerCase().includes(q) ||
        e.pid.toString().includes(q)
      );
    }
    return true;
  });

  const getSourceBadgeClass = (source: SourceType) => {
    switch (source) {
      case 'DETECTION ENGINE':
        return 'bg-[#93000a]/20 text-[#ffb4ab] border-[#ffb4ab]/30';
      case 'FILE MONITOR':
        return 'bg-[#df7412]/20 text-[#ffb786] border-[#ffb786]/30';
      case 'NETWORK MONITOR':
        return 'bg-[#4d8eff]/20 text-[#adc6ff] border-[#adc6ff]/30';
      case 'PROCESS MONITOR':
        return 'bg-[#00a572]/20 text-[#4edea3] border-[#4edea3]/30';
      default:
        return 'bg-[#272a31] text-[#c2c6d6] border-[#424754]';
    }
  };

  const getSeverityPip = (sev: SeverityType) => {
    switch (sev) {
      case 'critical':
        return <span className="w-2 h-2 rounded-full bg-[#ffb4ab] animate-pulse shadow-[0_0_8px_rgba(255,180,171,0.8)]" />;
      case 'high':
        return <span className="w-2 h-2 rounded-full bg-[#ffb786]" />;
      case 'medium':
        return <span className="w-2 h-2 rounded-full bg-[#adc6ff]" />;
      case 'low':
      case 'info':
      default:
        return <span className="w-1.5 h-1.5 rounded-full bg-[#8c909f]" />;
    }
  };

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[#1d2027] border border-[#424754] flex items-center justify-center text-[#adc6ff]">
            <Zap className="w-5 h-5 text-[#adc6ff]" />
          </div>
          <div>
            <h1 className="text-[24px] font-bold text-[#e1e2ec] leading-none">Live Events Stream</h1>
            <div className="font-mono text-[11px] text-[#c2c6d6] mt-1">
              Filtering:{' '}
              <span className="text-[#adc6ff] font-semibold">{selectedSource}</span> | Severity:{' '}
              <span className="text-[#adc6ff] font-semibold">{selectedSeverity}</span> | Search:{' '}
              <span className="text-[#e1e2ec]">{searchQuery || 'None'}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Stream Active Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#272a31] rounded border border-[#424754]">
            <span
              className={`w-2 h-2 rounded-full ${
                systemStatus.streamActive ? 'bg-[#4edea3] animate-pulse' : 'bg-[#8c909f]'
              }`}
            />
            <span className="font-mono text-[10px] font-bold text-[#4edea3] tracking-widest uppercase">
              {systemStatus.streamActive ? 'STREAM ACTIVE' : 'STREAM PAUSED'}
            </span>
          </div>

          {/* Filter Popover Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#1d2027] rounded border border-[#424754] cursor-pointer hover:bg-[#272a31] transition-colors font-mono text-[10px] font-bold text-[#e1e2ec]"
            >
              <Filter className="w-3.5 h-3.5 text-[#c2c6d6]" />
              <span>FILTER</span>
              <ChevronDown className="w-3 h-3 text-[#c2c6d6]" />
            </button>

            {showFilterDropdown && (
              <div className="absolute right-0 mt-2 w-72 bg-[#191b23] border border-[#424754] rounded shadow-2xl p-3 z-50 font-mono text-[11px] space-y-3">
                <div>
                  <div className="text-[10px] text-[#8c909f] font-bold uppercase mb-1.5">
                    Filter by Severity
                  </div>
                  <div className="grid grid-cols-3 gap-1">
                    {(['ALL', 'critical', 'high', 'medium', 'info'] as const).map((sev) => (
                      <button
                        key={sev}
                        onClick={() => setSelectedSeverity(sev)}
                        className={`px-2 py-1 rounded text-center text-[10px] uppercase font-bold border ${
                          selectedSeverity === sev
                            ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                            : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                        }`}
                      >
                        {sev}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-[#8c909f] font-bold uppercase mb-1.5">
                    Filter by Source
                  </div>
                  <div className="space-y-1">
                    {(
                      [
                        'ALL',
                        'DETECTION ENGINE',
                        'FILE MONITOR',
                        'NETWORK MONITOR',
                        'PROCESS MONITOR',
                      ] as const
                    ).map((src) => (
                      <button
                        key={src}
                        onClick={() => setSelectedSource(src)}
                        className={`w-full text-left px-2 py-1 rounded text-[10px] uppercase font-medium border ${
                          selectedSource === src
                            ? 'bg-[#adc6ff] text-[#002e6a] border-[#adc6ff]'
                            : 'bg-[#10131a] text-[#c2c6d6] border-[#424754] hover:bg-[#272a31]'
                        }`}
                      >
                        {src}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-[#424754] flex justify-between">
                  <button
                    onClick={() => {
                      setSelectedSeverity('ALL');
                      setSelectedSource('ALL');
                      setSearchQuery('');
                      setShowFilterDropdown(false);
                    }}
                    className="text-[10px] text-[#8c909f] hover:text-[#e1e2ec]"
                  >
                    Reset Filters
                  </button>
                  <button
                    onClick={() => setShowFilterDropdown(false)}
                    className="text-[10px] text-[#adc6ff] font-bold"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Pause / Resume Button */}
          <button
            onClick={toggleStream}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#1d2027] rounded border border-[#424754] cursor-pointer hover:bg-[#272a31] transition-colors font-mono text-[10px] font-bold text-[#e1e2ec]"
          >
            {systemStatus.streamActive ? (
              <>
                <Pause className="w-3.5 h-3.5 text-[#c2c6d6]" />
                <span>PAUSE</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-[#4edea3]" />
                <span>RESUME</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stats Bar (4 columns) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* EPS */}
        <div className="bg-[#1d2027] border border-[#424754] p-3.5 rounded flex flex-col justify-between">
          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            EVENTS/SEC (EPS)
          </div>
          <div className="text-[24px] font-bold text-[#e1e2ec] mt-1 flex items-baseline gap-2 font-mono">
            {systemStatus.eps.toLocaleString()}{' '}
            <span className="font-mono text-[11px] text-[#4edea3]">↑ 12%</span>
          </div>
          <div className="w-full h-8 mt-1 relative">
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 30">
              <polyline
                className="text-[#adc6ff] opacity-60"
                fill="none"
                points="0,25 10,22 20,28 30,15 40,18 50,5 60,12 70,8 80,15 90,4 100,10"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          </div>
        </div>

        {/* Detection Engine */}
        <div className="bg-[#1d2027] border border-[#424754] p-3.5 rounded flex flex-col justify-between relative overflow-hidden">
          <div className="absolute right-3 top-3 w-8 h-8 rounded-full border-2 border-[#4edea3] flex items-center justify-center">
            <span className="font-mono text-[8px] font-bold text-[#4edea3]">99%</span>
          </div>
          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            DETECTION ENGINE
          </div>
          <div className="text-[24px] font-bold text-[#e1e2ec] mt-1 font-mono">ONLINE</div>
          <div className="font-mono text-[11px] text-[#c2c6d6] mt-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />
            Latency: 14ms
          </div>
        </div>

        {/* Active Processes */}
        <div className="bg-[#1d2027] border border-[#424754] p-3.5 rounded flex flex-col justify-between">
          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            ACTIVE PROCESSES
          </div>
          <div className="text-[24px] font-bold text-[#e1e2ec] mt-1 flex items-baseline gap-2 font-mono">
            {systemStatus.activeProcessesCount}{' '}
            <span className="font-mono text-[11px] text-[#ffb4ab]">
              ↑ {systemStatus.suspiciousProcessesCount} (suspicious)
            </span>
          </div>
          <div className="w-full bg-[#272a31] h-1.5 mt-3 rounded overflow-hidden">
            <div
              className="bg-[#ffb4ab] h-full transition-all duration-500"
              style={{ width: `${Math.min(100, (systemStatus.suspiciousProcessesCount / 15) * 100)}%` }}
            />
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="bg-[#93000a] border border-[#ffb4ab] p-3.5 rounded flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 bg-[#ffb4ab]/5 animate-pulse rounded pointer-events-none" />
          <div className="font-mono text-[10px] font-bold text-[#ffdad6] tracking-wider uppercase">
            CRITICAL ALERTS
          </div>
          <div className="text-[24px] font-bold text-[#ffdad6] mt-1 font-mono">
            {systemStatus.criticalAlertsCount}
          </div>
          <div className="font-mono text-[11px] text-[#ffdad6]/80 mt-2">
            Requires immediate action
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-2 bg-[#191b23] border border-[#424754] rounded px-3 py-1.5">
        <Search className="w-4 h-4 text-[#8c909f]" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter live event stream by process, PID, artifact, indicator..."
          className="bg-transparent border-none outline-none font-mono text-[12px] text-[#e1e2ec] placeholder-[#8c909f] w-full"
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} className="text-[#8c909f] hover:text-[#e1e2ec]">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Data Table Container */}
      <div className="flex-1 bg-[#191b23] border border-[#424754] rounded flex flex-col overflow-hidden relative">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-1 p-2 bg-[#1d2027] border-b border-[#424754] sticky top-0 z-10 font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
          <div className="col-span-2 px-2 py-1">TIME (UTC)</div>
          <div className="col-span-2 px-2 py-1">SOURCE</div>
          <div className="col-span-2 px-2 py-1">EVENT</div>
          <div className="col-span-3 px-2 py-1">INDICATOR / ARTIFACT</div>
          <div className="col-span-1 px-2 py-1 text-right">PID</div>
          <div className="col-span-1 px-2 py-1">PROCESS</div>
          <div className="col-span-1 px-2 py-1 text-center">SEV</div>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden font-mono text-[11px] text-[#e1e2ec] divide-y divide-[#424754]/30 max-h-[480px]">
          {filteredEvents.map((evt) => {
            const isCriticalRow = evt.sev === 'critical';
            return (
              <div
                key={evt.id}
                onClick={() => setInspectEvent(evt)}
                className={`grid grid-cols-12 gap-1 p-2 hover:bg-[#272a31] transition-colors items-center cursor-pointer ${
                  isCriticalRow ? 'bg-[#93000a]/15 border-l-2 border-l-[#ffb4ab]' : ''
                }`}
              >
                <div className="col-span-2 px-2 py-0.5 text-[#c2c6d6] truncate font-medium">
                  {evt.time}
                </div>
                <div className="col-span-2 px-2 py-0.5">
                  <span
                    className={`inline-block px-2 py-0.5 border rounded text-[9px] font-mono font-bold ${getSourceBadgeClass(
                      evt.source
                    )}`}
                  >
                    {evt.source}
                  </span>
                </div>
                <div
                  className={`col-span-2 px-2 py-0.5 truncate font-semibold ${
                    isCriticalRow ? 'text-[#ffb4ab]' : evt.sev === 'high' ? 'text-[#ffb786]' : 'text-[#e1e2ec]'
                  }`}
                >
                  {evt.event}
                </div>
                <div className="col-span-3 px-2 py-0.5 truncate text-[#c2c6d6]">
                  {evt.indicator}
                </div>
                <div className="col-span-1 px-2 py-0.5 text-right text-[#c2c6d6]">
                  {evt.pid}
                </div>
                <div className="col-span-1 px-2 py-0.5 truncate text-[#adc6ff] font-medium">
                  {evt.process}
                </div>
                <div className="col-span-1 px-2 py-0.5 flex justify-center">
                  {getSeverityPip(evt.sev)}
                </div>
              </div>
            );
          })}

          {filteredEvents.length === 0 && (
            <div className="p-8 text-center text-[#8c909f] font-mono text-[12px]">
              No events matched the selected filter criteria.
            </div>
          )}
        </div>

        {/* Table Footer */}
        <div className="p-2 border-t border-[#424754] bg-[#1d2027] flex justify-between items-center px-4 h-9">
          <span className="font-mono text-[11px] text-[#c2c6d6] flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            Live Buffer: {filteredEvents.length} events logged
          </span>
          <button
            onClick={clearEvents}
            className="font-mono text-[10px] text-[#8c909f] hover:text-[#e1e2ec] uppercase"
          >
            Clear Buffer
          </button>
        </div>
      </div>

      {/* Inspect Event Modal */}
      {inspectEvent && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-[#191b23] border border-[#424754] rounded-lg max-w-lg w-full p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#424754] pb-3">
              <div className="flex items-center gap-2">
                <Info className="w-5 h-5 text-[#adc6ff]" />
                <h3 className="text-[16px] font-bold text-[#e1e2ec]">Event Artifact Inspector</h3>
              </div>
              <button
                onClick={() => setInspectEvent(null)}
                className="text-[#8c909f] hover:text-[#e1e2ec]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-[11px]">
              <div className="bg-[#10131a] p-3 rounded border border-[#424754] space-y-1.5">
                <div className="text-[#8c909f] text-[9px] uppercase font-bold">Event & Timestamp</div>
                <div className="text-[#e1e2ec] font-bold text-[13px]">{inspectEvent.event}</div>
                <div className="text-[#c2c6d6]">{inspectEvent.time} UTC</div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-[#10131a] p-2.5 rounded border border-[#424754]">
                  <div className="text-[#8c909f] text-[9px] uppercase">Process Name</div>
                  <div className="text-[#adc6ff] font-bold">{inspectEvent.process}</div>
                </div>
                <div className="bg-[#10131a] p-2.5 rounded border border-[#424754]">
                  <div className="text-[#8c909f] text-[9px] uppercase">Process ID (PID)</div>
                  <div className="text-[#e1e2ec] font-bold">{inspectEvent.pid}</div>
                </div>
              </div>

              <div className="bg-[#10131a] p-3 rounded border border-[#424754]">
                <div className="text-[#8c909f] text-[9px] uppercase font-bold mb-1">Indicator & Payload</div>
                <div className="text-[#e1e2ec] break-all">{inspectEvent.indicator}</div>
              </div>

              {inspectEvent.entropy && (
                <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
                  <span className="text-[#8c909f]">Calculated Shannon Entropy:</span>
                  <span className="text-[#ffb4ab] font-bold text-[13px]">
                    {inspectEvent.entropy} (Encrypted Threshold &gt; 7.8)
                  </span>
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-[#424754] flex gap-2">
              <button
                onClick={() => {
                  const proc = processes.find((p) => p.pid === inspectEvent.pid);
                  if (proc) {
                    setSelectedProcess(proc);
                    setActiveTab('process-activity');
                  }
                  setInspectEvent(null);
                }}
                className="flex-1 bg-[#adc6ff] text-[#002e6a] font-mono text-[11px] font-bold py-2 rounded flex items-center justify-center gap-1.5 hover:bg-[#d8e2ff]"
              >
                Inspect Associated Process <ExternalLink className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setInspectEvent(null)}
                className="px-4 bg-[#272a31] text-[#e1e2ec] font-mono text-[11px] rounded hover:bg-[#32353c]"
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
