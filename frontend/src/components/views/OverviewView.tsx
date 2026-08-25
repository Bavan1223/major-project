import React from 'react';
import { useSoc } from '../../context/SocContext';
import {
  ShieldCheck,
  MemoryStick as MemoryIcon,
  TrendingUp,
  Minus,
  FolderOpen,
  Network,
  Terminal,
  AlertTriangle,
  FileText,
  Activity,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

export const OverviewView: React.FC = () => {
  const {
    systemStatus,
    behavioralTelemetry,
    events,
    setActiveTab,
    setSelectedProcess,
    processes,
  } = useSoc();

  /*
   * ==========================================================
   * REAL BACKEND RISK STATE
   * ==========================================================
   */

  const isCritical =
    systemStatus.threatState === 'critical';

  const isHighRisk =
    systemStatus.threatState === 'high';

  const hasElevatedRisk =
    isCritical || isHighRisk;

  /*
   * ==========================================================
   * REAL TELEMETRY COUNTS
   * ==========================================================
   */

  const fileEventCount =
    events.filter(
      (event) =>
        event.source === 'FILE MONITOR'
    ).length;

  const networkEventCount =
    events.filter(
      (event) =>
        event.source === 'NETWORK MONITOR'
    ).length;

  const processEventCount =
    events.filter(
      (event) =>
        event.source === 'PROCESS MONITOR'
    ).length;

  const detectionAlertCount =
    systemStatus.criticalAlertsCount ||
    events.filter(
      (event) =>
        event.source === 'DETECTION ENGINE'
    ).length;

  /*
   * ==========================================================
   * MAIN UI
   * ==========================================================
   */

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">

      {/* ======================================================
          TOP BANNER
          ====================================================== */}

      <div className="grid grid-cols-12 gap-3">

        {/* Risk Status */}

        <div
          className={`col-span-12 lg:col-span-8 bg-[#1d2027] shadow-md rounded p-4 border relative overflow-hidden flex flex-col justify-center ${
            hasElevatedRisk
              ? 'border-[#ffb4ab] bg-[#93000a]/10'
              : 'border-[#424754]'
          }`}
        >

          <div className="absolute top-0 right-0 p-4 flex items-center gap-2">

            <span
              className={`w-2 h-2 rounded-full animate-pulse ${
                hasElevatedRisk
                  ? 'bg-[#ffb4ab]'
                  : 'bg-[#4edea3]'
              }`}
            />

            <span
              className={`font-mono text-[11px] tracking-widest uppercase ${
                hasElevatedRisk
                  ? 'text-[#ffb4ab]'
                  : 'text-[#4edea3]'
              }`}
            >
              {isCritical
                ? 'CRITICAL INCIDENT'
                : isHighRisk
                  ? 'HIGH RISK'
                  : 'LIVE'}
            </span>

          </div>

          <div className="flex items-center gap-6 z-10">

            <div
              className={`w-24 h-24 rounded-full border flex items-center justify-center relative shrink-0 ${
                hasElevatedRisk
                  ? 'border-[#ffb4ab] bg-[#ffb4ab]/10 text-[#ffb4ab]'
                  : 'border-[#4edea3] bg-[#4edea3]/10 text-[#4edea3]'
              }`}
            >

              {hasElevatedRisk ? (
                <ShieldAlert className="w-12 h-12 text-[#ffb4ab] animate-pulse" />
              ) : (
                <ShieldCheck className="w-12 h-12 text-[#4edea3]" />
              )}

              <svg
                className="absolute inset-0 w-full h-full -rotate-90"
                viewBox="0 0 100 100"
              >

                <circle
                  className={
                    hasElevatedRisk
                      ? 'text-[#ffb4ab]/20'
                      : 'text-[#4edea3]/20'
                  }
                  cx="50"
                  cy="50"
                  fill="none"
                  r="46"
                  stroke="currentColor"
                  strokeWidth="3"
                />

                <circle
                  className={`${
                    hasElevatedRisk
                      ? 'text-[#ffb4ab]'
                      : 'text-[#4edea3]'
                  } transition-all duration-1000`}
                  cx="50"
                  cy="50"
                  fill="none"
                  r="46"
                  stroke="currentColor"
                  strokeDasharray="289"
                  strokeDashoffset={
                    hasElevatedRisk
                      ? '40'
                      : '0'
                  }
                  strokeWidth="3"
                />

              </svg>

            </div>

            <div>

              <h2
                className={`text-[24px] font-bold tracking-tight mb-1.5 ${
                  hasElevatedRisk
                    ? 'text-[#ffb4ab]'
                    : 'text-[#4edea3]'
                }`}
              >
                {isCritical
                  ? 'RANSOMWARE BEHAVIOR DETECTED'
                  : isHighRisk
                    ? 'HIGH RISK DETECTED'
                    : 'SYSTEM NORMAL'}
              </h2>

              <p className="text-[14px] text-[#c2c6d6] max-w-xl leading-relaxed">

                {isCritical
                  ? 'Critical ransomware-like behavioral activity detected. Immediate response and containment is recommended.'
                  : isHighRisk
                    ? 'High-risk behavioral activity detected by the protection policy. Continuous monitoring is active in SAFE / DRY-RUN mode.'
                    : 'No high-confidence ransomware-like activity detected across monitored endpoints. Continuous behavioral analysis is active.'}

              </p>

            </div>

          </div>

          <div
            className={`absolute -right-20 -bottom-20 w-64 h-64 rounded-full blur-3xl pointer-events-none ${
              hasElevatedRisk
                ? 'bg-[#ffb4ab]/10'
                : 'bg-[#4edea3]/5'
            }`}
          />

        </div>


        {/* ====================================================
            DETECTION ENGINE
            ==================================================== */}

        <div className="col-span-12 lg:col-span-4 bg-[#1d2027] shadow-md rounded p-4 border border-[#424754] flex flex-col justify-between">

          <div className="flex items-center justify-between border-b border-[#424754] pb-2">

            <div className="flex items-center gap-2">

              <MemoryIcon className="w-4 h-4 text-[#adc6ff]" />

              <span className="font-mono text-[10px] font-bold text-[#e1e2ec] tracking-wider uppercase">
                DETECTION ENGINE
              </span>

            </div>

            <span className="font-mono text-[10px] text-[#4edea3] bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/30">
              ONLINE
            </span>

          </div>


          <div className="flex justify-between items-end mt-3">

            <div className="space-y-2.5 flex-1 pr-2">

              <div className="flex items-center justify-between">

                <span className="font-mono text-[11px] text-[#c2c6d6]">
                  RULE ENGINE
                </span>

                <span className="font-mono text-[11px] text-[#4edea3] bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/30">
                  ACTIVE
                </span>

              </div>


              <div className="flex items-center justify-between">

                <span className="font-mono text-[11px] text-[#c2c6d6]">
                  ML ENGINE
                </span>

                <span className="font-mono text-[11px] text-[#4edea3] bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/30">
                  ONLINE
                </span>

              </div>


              <div className="flex items-center justify-between">

                <span className="font-mono text-[11px] text-[#c2c6d6]">
                  CANARY TRAPS
                </span>

                <span className="font-mono text-[11px] text-[#adc6ff] bg-[#4d8eff]/20 px-2 py-0.5 rounded border border-[#adc6ff]/30">
                  12 ARMED
                </span>

              </div>

            </div>


            {/* Confidence */}

            <div className="ml-4 flex flex-col items-center justify-center shrink-0">

              <div className="relative w-16 h-16 flex items-center justify-center">

                <svg
                  className="w-16 h-16 transform -rotate-90"
                  viewBox="0 0 36 36"
                >

                  <path
                    className="text-[#272a31] stroke-current"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeWidth="3.2"
                  />

                  <path
                    className={`${
                      hasElevatedRisk
                        ? 'text-[#ffb4ab]'
                        : 'text-[#4edea3]'
                    } stroke-current`}
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeDasharray="99.64, 100"
                    strokeLinecap="round"
                    strokeWidth="3.2"
                  />

                </svg>

                <div className="absolute inset-0 flex items-center justify-center flex-col">

                  <span className="font-mono text-[13px] font-bold text-[#e1e2ec] leading-none">
                    {systemStatus.confidence > 0
                      ? systemStatus.confidence.toFixed(1)
                      : '0.0'}
                    <span className="text-[10px]">
                      %
                    </span>
                  </span>

                </div>

              </div>

              <span className="font-mono text-[9px] text-[#c2c6d6] mt-1.5 uppercase font-bold tracking-wider">
                CONFIDENCE
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* ======================================================
          TELEMETRY CARDS
          ====================================================== */}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">

        {/* FILE EVENTS */}

        <div
          onClick={() => setActiveTab('file-activity')}
          className="bg-[#1d2027] border border-[#424754] rounded p-3.5 flex flex-col hover:bg-[#272a31] transition-colors group cursor-pointer"
        >

          <div className="flex items-center justify-between mb-3">

            <FolderOpen className="w-5 h-5 text-[#adc6ff]" />

            <TrendingUp className="w-4 h-4 text-[#4edea3]" />

          </div>

          <div className="font-mono text-[22px] font-bold text-[#e1e2ec] mb-0.5">
            {fileEventCount}
          </div>

          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            FILE EVENTS
          </div>

        </div>


        {/* NETWORK EVENTS */}

        <div
          onClick={() => setActiveTab('network-activity')}
          className="bg-[#1d2027] border border-[#424754] rounded p-3.5 flex flex-col hover:bg-[#272a31] transition-colors group cursor-pointer"
        >

          <div className="flex items-center justify-between mb-3">

            <Network className="w-5 h-5 text-[#ffb786]" />

            <Minus className="w-4 h-4 text-[#c2c6d6]" />

          </div>

          <div className="font-mono text-[22px] font-bold text-[#e1e2ec] mb-0.5">
            {networkEventCount}
          </div>

          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            NETWORK EVENTS
          </div>

        </div>


        {/* PROCESS EVENTS */}

        <div
          onClick={() => setActiveTab('process-activity')}
          className="bg-[#1d2027] border border-[#424754] rounded p-3.5 flex flex-col hover:bg-[#272a31] transition-colors group cursor-pointer"
        >

          <div className="flex items-center justify-between mb-3">

            <Terminal className="w-5 h-5 text-[#adc6ff]" />

            <TrendingUp className="w-4 h-4 text-[#4edea3]" />

          </div>

          <div className="font-mono text-[22px] font-bold text-[#e1e2ec] mb-0.5">
            {processEventCount}
          </div>

          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            PROCESS EVENTS
          </div>

        </div>


        {/* DETECTION ALERTS */}

        <div
          onClick={() => setActiveTab('detection-risk')}
          className={`border rounded p-3.5 flex flex-col hover:bg-[#272a31] transition-colors group cursor-pointer ${
            hasElevatedRisk
              ? 'bg-[#93000a]/20 border-[#ffb4ab]'
              : 'bg-[#1d2027] border-[#424754]'
          }`}
        >

          <div className="flex items-center justify-between mb-3">

            <AlertTriangle
              className={`w-5 h-5 ${
                hasElevatedRisk
                  ? 'text-[#ffb4ab]'
                  : 'text-[#8c909f]'
              }`}
            />

            <div
              className={`w-2 h-2 rounded-full ${
                hasElevatedRisk
                  ? 'bg-[#ffb4ab] animate-ping'
                  : 'bg-[#4edea3]'
              }`}
            />

          </div>

          <div
            className={`font-mono text-[22px] font-bold mb-0.5 ${
              hasElevatedRisk
                ? 'text-[#ffb4ab]'
                : 'text-[#e1e2ec]'
            }`}
          >
            {detectionAlertCount}
          </div>

          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            DETECTION ALERTS
          </div>

        </div>


        {/* UNIQUE FILES */}

        <div
          onClick={() => setActiveTab('file-activity')}
          className="bg-[#1d2027] border border-[#424754] rounded p-3.5 flex flex-col hover:bg-[#272a31] transition-colors group cursor-pointer"
        >

          <div className="flex items-center justify-between mb-3">

            <FileText className="w-5 h-5 text-[#adc6ff]" />

            <Minus className="w-4 h-4 text-[#c2c6d6]" />

          </div>

          <div className="font-mono text-[22px] font-bold text-[#e1e2ec] mb-0.5">
            {behavioralTelemetry.filesModified}
          </div>

          <div className="font-mono text-[10px] font-bold text-[#c2c6d6] tracking-wider uppercase">
            UNIQUE FILES MODIFIED
          </div>

        </div>

      </div>


      {/* ======================================================
          LOWER SECTION
          ====================================================== */}

      <div className="grid grid-cols-12 gap-3 flex-1 min-h-[320px]">


        {/* BEHAVIORAL TELEMETRY */}

        <div className="col-span-12 lg:col-span-4 bg-[#1d2027] border border-[#424754] rounded flex flex-col overflow-hidden">

          <div className="p-3.5 border-b border-[#424754] flex items-center justify-between bg-[#1d2027]/70">

            <div className="flex items-center gap-2">

              <Activity className="w-4 h-4 text-[#adc6ff]" />

              <span className="font-mono text-[10px] font-bold text-[#e1e2ec] tracking-wider uppercase">
                BEHAVIORAL TELEMETRY
              </span>

            </div>

            <span className="font-mono text-[11px] text-[#c2c6d6]">
              Last 5 min
            </span>

          </div>


          <div className="flex-1 overflow-y-auto">

            <table className="w-full text-left font-mono">

              <tbody className="divide-y divide-[#424754]/40">

                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Files Created
                  </td>

                  <td className="px-4 py-3 text-[13px] font-bold text-[#e1e2ec] text-right">
                    {behavioralTelemetry.filesCreated}
                  </td>

                </tr>


                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Files Modified
                  </td>

                  <td className="px-4 py-3 text-[13px] font-bold text-[#e1e2ec] text-right">
                    {behavioralTelemetry.filesModified}
                  </td>

                </tr>


                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Files Deleted
                  </td>

                  <td className="px-4 py-3 text-[13px] font-bold text-[#e1e2ec] text-right">
                    {behavioralTelemetry.filesDeleted}
                  </td>

                </tr>


                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Files Renamed
                  </td>

                  <td className="px-4 py-3 text-[13px] font-bold text-[#e1e2ec] text-right">
                    {behavioralTelemetry.filesRenamed}
                  </td>

                </tr>


                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Network Conns
                  </td>

                  <td className="px-4 py-3 text-[13px] font-bold text-[#e1e2ec] text-right">
                    {behavioralTelemetry.networkConns}
                  </td>

                </tr>


                <tr className="hover:bg-[#272a31] transition-colors">

                  <td className="px-4 py-3 text-[12px] text-[#c2c6d6]">
                    Entropy Avg
                  </td>

                  <td
                    className={`px-4 py-3 text-[13px] font-bold text-right ${
                      behavioralTelemetry.entropyAvg > 7.0
                        ? 'text-[#ffb4ab]'
                        : 'text-[#4edea3]'
                    }`}
                  >
                    {behavioralTelemetry.entropyAvg.toFixed(2)}
                  </td>

                </tr>

              </tbody>

            </table>

          </div>

        </div>


        {/* ====================================================
            THREAT + LIVE STREAM
            ==================================================== */}

        <div className="col-span-12 lg:col-span-8 flex flex-col gap-3">

          {/* THREAT CARD */}

          {hasElevatedRisk ? (

            <div
              onClick={() =>
                setActiveTab('detection-risk')
              }
              className="bg-[#93000a]/15 border border-[#ffb4ab] rounded p-4 flex items-center justify-between cursor-pointer hover:bg-[#93000a]/25 transition-colors"
            >

              <div className="flex items-center gap-4">

                <div className="w-12 h-12 rounded bg-[#ffb4ab]/20 border border-[#ffb4ab] flex items-center justify-center text-[#ffb4ab]">

                  <AlertTriangle className="w-6 h-6 animate-pulse" />

                </div>

                <div>

                  <div className="text-[16px] font-bold text-[#ffb4ab]">

                    {isCritical
                      ? 'CRITICAL RANSOMWARE ACTIVITY DETECTED'
                      : 'HIGH-RISK ACTIVITY DETECTED'}

                  </div>

                  <div className="text-[12px] text-[#ffdad6] font-mono mt-0.5">

                    Backend detection state:{' '}
                    {systemStatus.threatState.toUpperCase()}
                    {' | '}
                    Alerts: {detectionAlertCount}
                    {' | '}
                    Mode:{' '}
                    {systemStatus.safeLabMode
                      ? 'SAFE / DRY-RUN'
                      : 'ACTIVE'}

                  </div>

                </div>

              </div>


              <button
                onClick={(e) => {

                  e.stopPropagation();

                  setActiveTab(
                    'detection-risk'
                  );

                }}
                className="px-3 py-1.5 bg-[#ffb4ab] text-[#690005] font-mono text-[11px] font-bold rounded shadow hover:bg-white transition-colors"
              >
                INVESTIGATE →
              </button>

            </div>

          ) : (

            <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col items-center justify-center relative overflow-hidden group">

              <div className="w-12 h-12 rounded-full border border-[#424754] flex items-center justify-center bg-[#10131a] mb-2">

                <ShieldCheck className="w-6 h-6 text-[#4edea3]" />

              </div>

              <div className="text-[16px] font-bold text-[#e1e2ec] mb-1">
                NO ACTIVE THREATS
              </div>

              <div className="text-[12px] text-[#c2c6d6] text-center max-w-sm">
                System is currently secure. No anomalous behavior or known ransomware signatures detected in the current window.
              </div>

            </div>

          )}


          {/* ==================================================
              LIVE EVENT STREAM
              ================================================== */}

          <div className="bg-[#1d2027] border border-[#424754] rounded overflow-hidden flex-1 flex flex-col">

            <div className="p-3.5 border-b border-[#424754] flex items-center justify-between bg-[#1d2027]/70">

              <div className="flex items-center gap-2">

                <Activity className="w-4 h-4 text-[#adc6ff]" />

                <span className="font-mono text-[10px] font-bold text-[#e1e2ec] tracking-wider uppercase">
                  LIVE EVENT STREAM
                </span>

              </div>

              <button
                onClick={() =>
                  setActiveTab('live-events')
                }
                className="text-[#adc6ff] hover:text-[#d8e2ff] transition-colors font-mono text-[11px] flex items-center gap-1 font-semibold"
              >
                VIEW ALL
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

            </div>


            <div className="overflow-x-auto flex-1">

              <table className="w-full text-left whitespace-nowrap font-mono text-[11px]">

                <thead>

                  <tr className="border-b border-[#424754] bg-[#10131a]/60 text-[#c2c6d6] text-[10px] uppercase font-bold tracking-wider">

                    <th className="px-4 py-2 w-32">
                      TIME (UTC)
                    </th>

                    <th className="px-4 py-2 w-24">
                      TYPE
                    </th>

                    <th className="px-4 py-2">
                      PROCESS
                    </th>

                    <th className="px-4 py-2">
                      DETAILS
                    </th>

                  </tr>

                </thead>


                <tbody className="divide-y divide-[#424754]/30 text-[#c2c6d6]">

                  {events
                    .slice(0, 4)
                    .map((evt) => (

                      <tr
                        key={evt.id}
                        onClick={() => {

                          const matchedProc =
                            processes.find(
                              (p) =>
                                p.pid ===
                                evt.pid
                            );

                          if (matchedProc) {
                            setSelectedProcess(
                              matchedProc
                            );
                          }

                          setActiveTab(
                            'live-events'
                          );

                        }}
                        className="hover:bg-[#272a31] transition-colors cursor-pointer"
                      >

                        <td className="px-4 py-2 text-[#e1e2ec]">
                          {evt.time}
                        </td>

                        <td className="px-4 py-2">

                          <span
                            className={`px-2 py-0.5 rounded border text-[9px] font-bold ${
                              evt.source ===
                              'DETECTION ENGINE'
                                ? 'bg-[#93000a]/20 border-[#ffb4ab]/30 text-[#ffb4ab]'
                                : evt.source ===
                                  'FILE MONITOR'
                                  ? 'bg-[#df7412]/20 border-[#ffb786]/30 text-[#ffb786]'
                                  : 'bg-[#4d8eff]/20 border-[#adc6ff]/30 text-[#adc6ff]'
                            }`}
                          >
                            {evt.source
                              .replace(
                                ' MONITOR',
                                ''
                              )
                              .replace(
                                ' ENGINE',
                                ''
                              )}
                          </span>

                        </td>

                        <td className="px-4 py-2 text-[#adc6ff] font-medium">
                          {evt.process}
                        </td>

                        <td className="px-4 py-2 truncate max-w-[280px] text-[#e1e2ec]">
                          {evt.indicator}
                        </td>

                      </tr>

                    ))}

                </tbody>

              </table>

            </div>

          </div>

        </div>

      </div>

    </div>
  );
};
