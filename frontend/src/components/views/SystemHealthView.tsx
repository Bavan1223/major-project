import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  Activity,
  Cpu,
  HardDrive,
  Server,
  Shield,
  CheckCircle,
  XCircle,
  RefreshCw,
} from 'lucide-react';

export const SystemHealthView: React.FC = () => {
  const { systemHealth, resetSimulation } = useSoc();

  const h = systemHealth;

  const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const isGood = status === 'ONLINE' || status === 'RUNNING' || status === 'AVAILABLE';
    return (
      <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded border flex items-center gap-1 ${
        isGood
          ? 'bg-[#00a572]/20 border-[#4edea3]/40 text-[#4edea3]'
          : 'bg-[#93000a]/20 border-[#ffb4ab]/40 text-[#ffb4ab]'
      }`}>
        {isGood ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
        {status}
      </span>
    );
  };

  const ProgressBar: React.FC<{ value: number; color: string }> = ({ value, color }) => (
    <div className="w-full h-2 bg-[#272a31] rounded overflow-hidden">
      <div className={`h-full rounded ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
    </div>
  );

  if (!h) {
    return (
      <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] items-center justify-center">
        <div className="text-[#8c909f] font-mono text-[12px]">Loading system health...</div>
      </div>
    );
  }

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Header */}
      <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-[#00a572]/20 border border-[#4edea3]/40 flex items-center justify-center text-[#4edea3]">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider">
              SYSTEM HEALTH MONITOR
            </div>
            <div className="text-[15px] font-bold text-[#e1e2ec]">
              Uptime: {formatUptime(h.uptime_seconds)}
            </div>
          </div>
        </div>
        <button
          onClick={resetSimulation}
          className="px-3 py-2 bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold rounded hover:bg-[#32353c] flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> REFRESH
        </button>
      </div>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Backend API</span>
            <StatusBadge status={h.backend} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">Flask server at :5000</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">File Monitor</span>
            <StatusBadge status={h.file_monitor} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">inotify watcher</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Process Monitor</span>
            <StatusBadge status={h.process_monitor} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">psutil process scanner</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Network Monitor</span>
            <StatusBadge status={h.network_monitor} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">Socket connection scanner</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Detection Pipeline</span>
            <StatusBadge status={h.detection_pipeline} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">Behavioral analysis loop</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Event Log</span>
            <StatusBadge status={h.event_log} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">logs/events.jsonl</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">ML Model</span>
            <StatusBadge status={h.ml_model} />
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">Random Forest v2.0.0</div>
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] text-[#8c909f] uppercase">Protection</span>
            <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded border bg-[#00a572]/20 border-[#4edea3]/40 text-[#4edea3] flex items-center gap-1">
              <Shield className="w-3 h-3" /> {h.protection_mode}
            </span>
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6]">Safe Lab: {h.safe_lab_mode ? 'ENABLED' : 'DISABLED'}</div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-[#1d2027] border border-[#424754] rounded p-4">
        <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider mb-4">
          HOST METRICS
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-[11px] text-[#c2c6d6] flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#adc6ff]" /> CPU Usage
              </span>
              <span className="font-mono text-[11px] text-[#e1e2ec] font-bold">{h.cpu_percent.toFixed(1)}%</span>
            </div>
            <ProgressBar value={h.cpu_percent} color="bg-[#adc6ff]" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-[11px] text-[#c2c6d6] flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-[#4edea3]" /> Memory Usage
              </span>
              <span className="font-mono text-[11px] text-[#e1e2ec] font-bold">{h.memory_percent.toFixed(1)}%</span>
            </div>
            <ProgressBar value={h.memory_percent} color="bg-[#4edea3]" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-[11px] text-[#c2c6d6] flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-[#ffb786]" /> Disk Usage
              </span>
              <span className="font-mono text-[11px] text-[#e1e2ec] font-bold">{h.disk_percent.toFixed(1)}%</span>
            </div>
            <ProgressBar value={h.disk_percent} color="bg-[#ffb786]" />
          </div>
        </div>
      </div>
    </div>
  );
};
