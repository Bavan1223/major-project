import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  Activity,
  CheckCircle2,
  Cpu,
  HardDrive,
  Clock,
  Shield,
  Server,
  Zap,
  Radio,
  FileCheck,
} from 'lucide-react';

export const SystemHealthView: React.FC = () => {
  const { systemStatus } = useSoc();

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">
      {/* Header */}
      <div className="flex justify-between items-center bg-[#1d2027] border border-[#424754] rounded p-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-[#4edea3]" />
            <h1 className="text-[20px] font-bold text-[#e1e2ec]">System &amp; Pipeline Health</h1>
          </div>
          <div className="font-mono text-[11px] text-[#c2c6d6] mt-0.5">
            Real-time telemetry collectors, detection microservices, and host subsystem statuses.
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-[#00a572]/20 border border-[#4edea3]/30 px-3 py-1 rounded flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse" />
            <span className="font-mono text-[10px] font-bold text-[#4edea3] uppercase tracking-wider">
              ALL SUBSYSTEMS HEALTHY
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Monitors & Collectors vs Engines */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Section 1: Monitors & Collectors */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#424754] pb-2">
            <span className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-4 h-4" /> INGESTION &amp; TELEMETRY COLLECTORS
            </span>
            <span className="font-mono text-[10px] text-[#4edea3]">3/3 RUNNING</span>
          </div>

          <div className="space-y-2 font-mono text-[11px]">
            {/* Collector 1 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">eBPF Kernel Ring Buffer</div>
                <div className="text-[#8c909f] text-[10px]">Hooked into sys_enter_write &amp; sys_enter_openat</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">2,408 EPS</span>
                <div className="text-[9px] text-[#4edea3] flex items-center gap-1 justify-end">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" /> HEALTHY
                </div>
              </div>
            </div>

            {/* Collector 2 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">VFS inotify File Stream</div>
                <div className="text-[#8c909f] text-[10px]">Tracking rapid create/rename cycles</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">120 evt/s</span>
                <div className="text-[9px] text-[#4edea3] flex items-center gap-1 justify-end">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" /> HEALTHY
                </div>
              </div>
            </div>

            {/* Collector 3 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">Network Socket Sniffer</div>
                <div className="text-[#8c909f] text-[10px]">Monitoring C2 outbound TCP handshakes</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">45 conns/s</span>
                <div className="text-[9px] text-[#4edea3] flex items-center gap-1 justify-end">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" /> HEALTHY
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Engines & Inference */}
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#424754] pb-2">
            <span className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="w-4 h-4" /> DETECTION ENGINES &amp; INFERENCE
            </span>
            <span className="font-mono text-[10px] text-[#4edea3]">3/3 RUNNING</span>
          </div>

          <div className="space-y-2 font-mono text-[11px]">
            {/* Engine 1 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">ML Classifier v2.0.0</div>
                <div className="text-[#8c909f] text-[10px]">AST Graph + Random Forest Ensemble</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">14ms latency</span>
                <div className="text-[9px] text-[#4edea3]">99.64% Conf.</div>
              </div>
            </div>

            {/* Engine 2 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">MITRE ATT&amp;CK Rule Engine</div>
                <div className="text-[#8c909f] text-[10px]">T1486, T1490, T1059, T1055 definitions</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">142 Rules</span>
                <div className="text-[9px] text-[#4edea3]">ACTIVE</div>
              </div>
            </div>

            {/* Engine 3 */}
            <div className="bg-[#10131a] p-3 rounded border border-[#424754] flex justify-between items-center">
              <div>
                <div className="text-[#e1e2ec] font-bold">Shannon Entropy Calculator</div>
                <div className="text-[#8c909f] text-[10px]">128-byte block statistical byte distribution</div>
              </div>
              <div className="text-right">
                <span className="text-[#4edea3] font-bold">100% Coverage</span>
                <div className="text-[9px] text-[#4edea3]">STREAMING</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Host Metrics & Uptime */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex items-center justify-between">
          <div>
            <div className="font-mono text-[10px] text-[#8c909f] uppercase font-bold">HOST UPTIME</div>
            <div className="text-[20px] font-bold font-mono text-[#e1e2ec] mt-1">14d 8h 22m 14s</div>
            <div className="text-[11px] text-[#4edea3] font-mono mt-0.5">Zero unhandled crashes</div>
          </div>
          <Clock className="w-8 h-8 text-[#8c909f]/40" />
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex items-center justify-between">
          <div className="w-full mr-4">
            <div className="font-mono text-[10px] text-[#8c909f] uppercase font-bold">HOST CPU LOAD</div>
            <div className="text-[20px] font-bold font-mono text-[#e1e2ec] mt-1">42% (8 Cores)</div>
            <div className="w-full bg-[#10131a] h-1.5 rounded-full overflow-hidden mt-2 border border-[#424754]">
              <div className="h-full bg-[#adc6ff] w-[42%]" />
            </div>
          </div>
          <Cpu className="w-8 h-8 text-[#8c909f]/40 shrink-0" />
        </div>

        <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex items-center justify-between">
          <div className="w-full mr-4">
            <div className="font-mono text-[10px] text-[#8c909f] uppercase font-bold">MEMORY USAGE</div>
            <div className="text-[20px] font-bold font-mono text-[#e1e2ec] mt-1">6.4 GB / 16.0 GB</div>
            <div className="w-full bg-[#10131a] h-1.5 rounded-full overflow-hidden mt-2 border border-[#424754]">
              <div className="h-full bg-[#ffb786] w-[40%]" />
            </div>
          </div>
          <HardDrive className="w-8 h-8 text-[#8c909f]/40 shrink-0" />
        </div>
      </div>
    </div>
  );
};
