import React, { useState, useEffect, useCallback } from 'react';
import { useSoc } from '../../context/SocContext';
import {
  AlertTriangle,
  ShieldAlert,
  Shield,
  Activity,
  CheckCircle,
  FileWarning,
  Brain,
  Zap,
  RotateCcw,
  Lock,
  Eye,
} from 'lucide-react';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'http://192.168.74.131:5000';

/*
 * Signal display metadata.
 * Maps backend signal names to human-readable labels.
 */
const SIGNAL_LABELS: Record<string, { label: string; description: string }> = {
  rapid_mass_file_modification: {
    label: 'Rapid Mass File Modification',
    description: 'Multiple files modified in rapid succession within the observation window.',
  },
  multiple_unique_files_modified: {
    label: 'Multiple Unique Files Modified',
    description: '10 or more unique files were modified in the behavioral window.',
  },
  ml_ransomware_confirmed: {
    label: 'ML Ransomware Classification Confirmed',
    description: 'Machine learning model confirmed ransomware-like behavioral pattern with high confidence.',
  },
  ml_ransomware_detected: {
    label: 'ML Ransomware Pattern Detected',
    description: 'ML model detected ransomware-like behavior (no rule-based confirmation).',
  },
};

/*
 * Risk level severity colors and labels.
 */
const RISK_CONFIG: Record<string, {
  bg: string;
  border: string;
  text: string;
  badge: string;
  label: string;
}> = {
  CRITICAL: {
    bg: 'bg-[#93000a]/20',
    border: 'border-[#ffb4ab]',
    text: 'text-[#ffb4ab]',
    badge: 'bg-[#93000a]',
    label: 'CRITICAL',
  },
  HIGH: {
    bg: 'bg-[#df7412]/15',
    border: 'border-[#ffb786]',
    text: 'text-[#ffb786]',
    badge: 'bg-[#df7412]/60',
    label: 'HIGH',
  },
  MEDIUM: {
    bg: 'bg-[#625b00]/15',
    border: 'border-[#e5c349]',
    text: 'text-[#e5c349]',
    badge: 'bg-[#625b00]/60',
    label: 'MEDIUM',
  },
  LOW: {
    bg: 'bg-[#1d2027]',
    border: 'border-[#424754]',
    text: 'text-[#adc6ff]',
    badge: 'bg-[#272a31]',
    label: 'LOW',
  },
  NORMAL: {
    bg: 'bg-[#1d2027]',
    border: 'border-[#4edea3]/40',
    text: 'text-[#4edea3]',
    badge: 'bg-[#00a572]/30',
    label: 'NORMAL',
  },
};

interface RiskData {
  risk_level: string;
  reason: string;
  signals: string[];
  detected: boolean;
  timestamp: string | null;
  ml_contributed?: boolean;
}

export const DetectionRiskView: React.FC = () => {
  const {
    systemStatus,
    triggerContainment,
    restoreHost,
    actionLogs,
  } = useSoc();

  const [riskData, setRiskData] = useState<RiskData>({
    risk_level: 'NORMAL',
    reason: 'No suspicious behavior detected.',
    signals: [],
    detected: false,
    timestamp: null,
  });

  const [statusData, setStatusData] = useState<any>(null);

  /*
   * Fetch real risk state from backend.
   */
  const fetchRisk = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/risk`, {
        cache: 'no-store',
      });
      if (!response.ok) return;
      const data = await response.json();
      setRiskData(data);
    } catch (error) {
      console.error('DetectionRiskView: risk fetch error', error);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`, {
        cache: 'no-store',
      });
      if (!response.ok) return;
      const data = await response.json();
      setStatusData(data);
    } catch (error) {
      console.error('DetectionRiskView: status fetch error', error);
    }
  }, []);

  useEffect(() => {
    fetchRisk();
    fetchStatus();
    const interval = window.setInterval(() => {
      fetchRisk();
      fetchStatus();
    }, 2000);
    return () => window.clearInterval(interval);
  }, [fetchRisk, fetchStatus]);

  const riskLevel = riskData.risk_level || 'NORMAL';
  const config = RISK_CONFIG[riskLevel] || RISK_CONFIG.NORMAL;
  const isActive = riskData.detected && riskLevel !== 'NORMAL' && riskLevel !== 'LOW';
  const mlConfidence = systemStatus.confidence || 0;
  const incidentCount = statusData?.detection_event_count || 0;
  const protectionMode = statusData?.protection_mode || 'DRY_RUN';

  const handleAuthorize = () => {
    triggerContainment();
  };

  return (
    <div className="flex flex-col w-full p-4 gap-3 bg-[#10131a] min-h-[calc(100vh-64px)] select-none">

      {/* Top Banner / Incident Header */}
      <div className={`${config.bg} border ${config.border} rounded p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden`}>
        <div className="flex items-center gap-4 z-10">
          <div className={`w-12 h-12 rounded ${config.bg} border ${config.border} flex items-center justify-center ${config.text} shrink-0`}>
            {isActive ? (
              <AlertTriangle className="w-7 h-7 animate-pulse" />
            ) : (
              <Shield className="w-7 h-7" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={`${config.badge} ${config.text} text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${config.border}/40`}>
                {config.label} SEVERITY
              </span>
              <span className="text-[#adc6ff] text-[10px] font-mono bg-[#191b23] px-2 py-0.5 rounded border border-[#424754]">
                HOST: 192.168.74.131
              </span>
              <span className="text-[#ffb786] text-[10px] font-mono bg-[#191b23] px-2 py-0.5 rounded border border-[#424754]">
                MODE: {protectionMode}
              </span>
              {systemStatus.hostIsolated && (
                <span className="text-[#4edea3] text-[10px] font-mono bg-[#00a572]/20 px-2 py-0.5 rounded border border-[#4edea3]/40 flex items-center gap-1 font-bold">
                  <CheckCircle className="w-3 h-3" /> CONTAINED (DRY-RUN)
                </span>
              )}
            </div>
            <h1 className={`text-[20px] font-bold ${config.text} tracking-tight`}>
              {isActive
                ? 'RANSOMWARE-LIKE BEHAVIORAL ACTIVITY DETECTED'
                : 'NO ACTIVE THREAT DETECTED — SYSTEM NORMAL'}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 z-10">
          {isActive && (
            systemStatus.hostIsolated ? (
              <button
                onClick={restoreHost}
                className="bg-[#272a31] border border-[#424754] text-[#e1e2ec] font-mono text-[11px] font-bold px-4 py-2 rounded hover:bg-[#32353c] flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" /> RESTORE HOST STATE
              </button>
            ) : (
              <button
                onClick={handleAuthorize}
                className="bg-[#ffb4ab] text-[#690005] font-mono text-[12px] font-bold px-5 py-2.5 rounded shadow-lg hover:bg-white transition-all flex items-center gap-2"
              >
                <Lock className="w-4 h-4" /> AUTHORIZE CONTAINMENT (DRY-RUN)
              </button>
            )
          )}
        </div>

        {/* Glow */}
        {isActive && (
          <div className="absolute right-0 top-0 w-96 h-96 bg-[#ffb4ab]/5 blur-3xl pointer-events-none" />
        )}
      </div>

      {/* Detection Reason */}
      <div className="bg-[#1d2027] border border-[#424754] rounded p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="font-mono text-[10px] font-bold text-[#adc6ff] uppercase tracking-widest flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" /> BEHAVIORAL ANALYSIS
          </div>
          <span className="font-mono text-[10px] text-[#c2c6d6]">
            Engine: Rule-Based + Random Forest ML
          </span>
        </div>
        <p className="text-[13px] text-[#e1e2ec] leading-relaxed font-mono">
          {riskData.reason}
        </p>
        {riskData.timestamp && (
          <p className="text-[10px] text-[#8c909f] font-mono">
            Last assessment: {riskData.timestamp}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] font-mono text-[#8c909f] bg-[#10131a] px-2 py-0.5 rounded border border-[#424754]">
            SAFE LAB MODE: ACTIVE
          </span>
          <span className="text-[10px] font-mono text-[#8c909f] bg-[#10131a] px-2 py-0.5 rounded border border-[#424754]">
            INCIDENTS DETECTED: {incidentCount}
          </span>
        </div>
      </div>

      {/* Middle 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">

        {/* Left: Triggered Signals */}
        <div className="lg:col-span-7 flex flex-col gap-3">
          <div className="bg-[#1d2027] border border-[#424754] rounded p-3.5 space-y-2.5">
            <div className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase tracking-wider mb-2">
              TRIGGERED BEHAVIORAL SIGNALS ({riskData.signals.length})
            </div>

            {riskData.signals.length === 0 && (
              <div className="bg-[#10131a] border border-[#4edea3]/30 rounded p-4 flex items-center gap-3">
                <div className="w-7 h-7 rounded bg-[#00a572]/20 border border-[#4edea3]/40 flex items-center justify-center text-[#4edea3] shrink-0">
                  <CheckCircle className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-[13px] text-[#4edea3]">
                    No Behavioral Signals Active
                  </span>
                  <div className="text-[11px] text-[#c2c6d6] mt-0.5 font-mono">
                    System operating within normal parameters.
                  </div>
                </div>
              </div>
            )}

            {riskData.signals.map((signal, idx) => {
              const info = SIGNAL_LABELS[signal] || {
                label: signal.replace(/_/g, ' ').toUpperCase(),
                description: `Behavioral signal: ${signal}`,
              };
              const isCritical = signal.includes('ml_ransomware_confirmed') || signal.includes('rapid_mass');
              return (
                <div
                  key={idx}
                  className={`bg-[#10131a] border ${
                    isCritical ? 'border-[#ffb4ab]/50' : 'border-[#ffb786]/50'
                  } rounded p-3 flex items-start gap-3`}
                >
                  <div className={`w-7 h-7 rounded ${
                    isCritical
                      ? 'bg-[#93000a]/40 border border-[#ffb4ab]'
                      : 'bg-[#df7412]/30 border border-[#ffb786]'
                  } flex items-center justify-center ${
                    isCritical ? 'text-[#ffb4ab]' : 'text-[#ffb786]'
                  } shrink-0 mt-0.5`}>
                    {signal.includes('ml_') ? (
                      <Brain className="w-4 h-4" />
                    ) : (
                      <FileWarning className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold text-[13px] ${
                        isCritical ? 'text-[#ffb4ab]' : 'text-[#ffb786]'
                      }`}>
                        {info.label}
                      </span>
                      <span className={`font-mono text-[10px] ${
                        isCritical ? 'text-[#ffb4ab] bg-[#93000a]/30' : 'text-[#ffb786] bg-[#df7412]/20'
                      } px-1.5 py-0.5 rounded border ${
                        isCritical ? 'border-[#ffb4ab]/30' : 'border-[#ffb786]/30'
                      }`}>
                        {isCritical ? 'CRITICAL' : 'HIGH'}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#c2c6d6] mt-0.5 font-mono">
                      {info.description}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Detection Summary Stats */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-3.5">
            <div className="font-mono text-[10px] font-bold text-[#c2c6d6] uppercase tracking-wider mb-3">
              SYSTEM TELEMETRY SUMMARY
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <div className="bg-[#10131a] rounded border border-[#424754] p-3 text-center">
                <div className="font-mono text-[18px] font-bold text-[#adc6ff]">
                  {statusData?.file_event_count || 0}
                </div>
                <div className="font-mono text-[9px] text-[#8c909f] uppercase">
                  File Events
                </div>
              </div>
              <div className="bg-[#10131a] rounded border border-[#424754] p-3 text-center">
                <div className="font-mono text-[18px] font-bold text-[#adc6ff]">
                  {statusData?.network_event_count || 0}
                </div>
                <div className="font-mono text-[9px] text-[#8c909f] uppercase">
                  Network Events
                </div>
              </div>
              <div className="bg-[#10131a] rounded border border-[#424754] p-3 text-center">
                <div className="font-mono text-[18px] font-bold text-[#adc6ff]">
                  {statusData?.process_event_count || 0}
                </div>
                <div className="font-mono text-[9px] text-[#8c909f] uppercase">
                  Process Events
                </div>
              </div>
              <div className="bg-[#10131a] rounded border border-[#424754] p-3 text-center">
                <div className={`font-mono text-[18px] font-bold ${
                  incidentCount > 0 ? 'text-[#ffb4ab]' : 'text-[#4edea3]'
                }`}>
                  {incidentCount}
                </div>
                <div className="font-mono text-[9px] text-[#8c909f] uppercase">
                  Incidents
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: ML Confidence & Response Info */}
        <div className="lg:col-span-5 flex flex-col gap-3">

          {/* ML Assessment Card */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-[#424754] pb-2">
              <span className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase">
                ML CLASSIFIER ASSESSMENT
              </span>
              <span className={`font-mono text-[9px] px-2 py-0.5 rounded border ${
                mlConfidence > 70
                  ? 'text-[#ffb4ab] bg-[#93000a]/20 border-[#ffb4ab]/30'
                  : mlConfidence > 0
                    ? 'text-[#e5c349] bg-[#625b00]/20 border-[#e5c349]/30'
                    : 'text-[#4edea3] bg-[#00a572]/20 border-[#4edea3]/30'
              }`}>
                {mlConfidence > 70
                  ? 'HIGH CONFIDENCE'
                  : mlConfidence > 0
                    ? 'LOW CONFIDENCE'
                    : 'NORMAL'}
              </span>
            </div>

            <div className="flex items-center justify-around my-4">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-[#272a31] stroke-current"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeWidth="3.5"
                  />
                  <path
                    className={`${
                      mlConfidence > 70 ? 'text-[#ffb4ab]' : 'text-[#4edea3]'
                    } stroke-current transition-all duration-1000`}
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    strokeDasharray={`${mlConfidence}, 100`}
                    strokeLinecap="round"
                    strokeWidth="3.5"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className={`font-mono text-[18px] font-bold ${
                    mlConfidence > 70 ? 'text-[#ffb4ab]' : 'text-[#4edea3]'
                  } leading-none`}>
                    {mlConfidence.toFixed(1)}%
                  </span>
                  <span className="font-mono text-[8px] text-[#c2c6d6] uppercase mt-0.5">
                    LIKELIHOOD
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 font-mono text-[10px]">
                <div className="text-[#8c909f]">
                  Model: <span className="text-[#e1e2ec] font-bold">Random Forest v2.0.0</span>
                </div>
                <div className="text-[#8c909f]">
                  Threshold: <span className="text-[#e1e2ec]">70% (0.7)</span>
                </div>
                <div className="text-[#8c909f]">
                  Classification:{' '}
                  <span className={mlConfidence > 70 ? 'text-[#ffb4ab] font-bold' : 'text-[#4edea3]'}>
                    {mlConfidence > 70 ? 'RANSOMWARE_LIKE' : 'NORMAL'}
                  </span>
                </div>
                <div className="text-[#8c909f]">
                  ML Contributed:{' '}
                  <span className="text-[#e1e2ec]">
                    {riskData.ml_contributed ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            <div className="text-[10px] font-mono text-[#8c909f] border-t border-[#424754] pt-2 mt-1">
              ML is advisory only. ML alone caps at MEDIUM severity.
              Rule HIGH + ML confident agreement = CRITICAL.
            </div>
          </div>

          {/* Response & Protection Status */}
          <div className="bg-[#1d2027] border border-[#424754] rounded p-4 flex flex-col flex-1">
            <div className="font-mono text-[10px] font-bold text-[#e1e2ec] uppercase tracking-wider mb-3">
              RESPONSE & PROTECTION STATUS
            </div>

            <div className="space-y-2 flex-1 font-mono text-[11px]">
              <div className="flex items-center gap-2 p-2.5 bg-[#10131a] rounded border border-[#424754]">
                <Eye className="w-4 h-4 text-[#adc6ff]" />
                <div className="flex-1">
                  <div className="text-[#e1e2ec] font-bold">Response Decision</div>
                  <div className="text-[#8c909f] text-[10px]">
                    {isActive
                      ? riskLevel === 'CRITICAL'
                        ? 'CRITICAL_RESPONSE_RESERVED'
                        : 'CONTAINMENT_RECOMMENDED'
                      : 'NO_ACTION'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2.5 bg-[#10131a] rounded border border-[#424754]">
                <ShieldAlert className="w-4 h-4 text-[#adc6ff]" />
                <div className="flex-1">
                  <div className="text-[#e1e2ec] font-bold">Protection Action</div>
                  <div className="text-[#8c909f] text-[10px]">
                    {isActive
                      ? riskLevel === 'CRITICAL'
                        ? 'CRITICAL_PROTECTION_RESERVED'
                        : 'LAB_CONTAINMENT_RECOMMENDED'
                      : 'NO_PROTECTION'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2.5 bg-[#10131a] rounded border border-[#424754]">
                <Shield className="w-4 h-4 text-[#4edea3]" />
                <div className="flex-1">
                  <div className="text-[#e1e2ec] font-bold">Protection Mode</div>
                  <div className="text-[#4edea3] text-[10px] font-bold">
                    DRY_RUN — No destructive actions executed
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 p-2.5 bg-[#10131a] rounded border border-[#424754]">
                <Zap className="w-4 h-4 text-[#e5c349]" />
                <div className="flex-1">
                  <div className="text-[#e1e2ec] font-bold">Safe Lab Mode</div>
                  <div className="text-[#4edea3] text-[10px]">
                    ACTIVE — Academic lab environment
                  </div>
                </div>
              </div>
            </div>

            {isActive && !systemStatus.hostIsolated && (
              <button
                onClick={handleAuthorize}
                className="w-full mt-4 font-mono text-[12px] font-bold py-2.5 rounded shadow flex items-center justify-center gap-2 transition-all bg-[#ffb4ab] text-[#690005] hover:bg-white"
              >
                <Lock className="w-4 h-4" /> AUTHORIZE CONTAINMENT (DRY-RUN)
              </button>
            )}

            {systemStatus.hostIsolated && (
              <div className="w-full mt-4 font-mono text-[12px] font-bold py-2.5 rounded shadow flex items-center justify-center gap-2 bg-[#00a572]/20 border border-[#4edea3] text-[#4edea3]">
                <CheckCircle className="w-4 h-4" /> CONTAINMENT ACKNOWLEDGED (DRY-RUN)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Action Log Terminal */}
      <div className="bg-[#0b0e15] border border-[#424754] rounded p-3 font-mono text-[11px] space-y-1 overflow-y-auto max-h-36">
        <div className="text-[#8c909f] text-[9px] uppercase font-bold border-b border-[#424754]/50 pb-1 mb-1">
          Audit Log &amp; Response Actions (DRY-RUN)
        </div>
        {actionLogs.length === 0 && (
          <div className="text-[#8c909f]">No actions recorded this session.</div>
        )}
        {actionLogs.map((log, idx) => (
          <div
            key={idx}
            className={
              log.includes('CONTAINMENT')
                ? 'text-[#4edea3] font-bold'
                : log.includes('CRITICAL') || log.includes('RANSOMWARE')
                  ? 'text-[#ffb4ab]'
                  : 'text-[#c2c6d6]'
            }
          >
            {log}
          </div>
        ))}
      </div>
    </div>
  );
};
