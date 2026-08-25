import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';

import {
  TabType,
  SocEvent,
  NetworkConnection,
  ProcessItem,
  FileActivityItem,
  BehavioralTelemetry,
  SystemStatus,
  Incident,
  AuditEntry,
  SystemHealth,
} from '../types';

// ============================================================
// BACKEND CONFIGURATION
// ============================================================

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'http://192.168.74.131:5000';

// ============================================================
// CONTEXT CONTRACT
// ============================================================

interface SocContextType {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  systemStatus: SystemStatus;
  setSystemStatus: React.Dispatch<React.SetStateAction<SystemStatus>>;
  events: SocEvent[];
  addEvent: (event: Omit<SocEvent, 'id'>) => void;
  clearEvents: () => void;
  toggleStream: () => void;
  connections: NetworkConnection[];
  processes: ProcessItem[];
  selectedProcess: ProcessItem | null;
  setSelectedProcess: (process: ProcessItem | null) => void;
  fileActivities: FileActivityItem[];
  behavioralTelemetry: BehavioralTelemetry;
  actionLogs: string[];
  currentTimeString: string;

  // Incidents
  incidents: Incident[];
  activeIncident: Incident | null;

  // Audit
  auditLog: AuditEntry[];

  // Health
  systemHealth: SystemHealth | null;

  // Backend Actions (all call real APIs)
  triggerContainment: () => Promise<void>;
  restoreHost: () => Promise<void>;
  killProcess: (pid: number) => Promise<void>;
  toggleSafeLabMode: () => void;
  simulateAttack: () => Promise<void>;
  resetSimulation: () => void;
  acknowledgeIncident: (id: string) => Promise<void>;
  containIncident: (id: string) => Promise<void>;
  resolveIncident: (id: string) => Promise<void>;
  closeIncident: (id: string) => Promise<void>;
  protectLabFiles: () => Promise<void>;
  isolateProcess: (pid?: number, process?: string) => Promise<void>;
  isolateNetwork: () => Promise<void>;
  createSnapshot: () => Promise<void>;
  restoreLabFiles: () => Promise<void>;
}

const SocContext = createContext<SocContextType | undefined>(undefined);

// ============================================================
// HELPERS
// ============================================================

function makeEventId(event: any, index: number): string {
  return [event?.timestamp || 'event', event?.pid ?? 'none', event?.event_type || 'unknown', index].join('-');
}

function formatTime(timestamp: string | undefined): string {
  if (!timestamp) return '--:--:--';
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toISOString().substring(11, 23);
  } catch {
    return timestamp;
  }
}

function getSeverity(event: any): string {
  const source = event?.source || '';
  const type = event?.event_type || '';
  const indicator = event?.indicator || '';
  const text = `${source} ${type} ${indicator}`.toLowerCase();
  if (source === 'detection_engine' || text.includes('critical') || text.includes('ransomware')) return 'critical';
  if (text.includes('suspicious') || text.includes('repeated') || text.includes('deletion') || text.includes('rename')) return 'high';
  if (source === 'network_monitor') return 'medium';
  return 'info';
}

function getSourceLabel(source: string | undefined): string {
  switch (source) {
    case 'file_monitor': return 'FILE MONITOR';
    case 'process_monitor': return 'PROCESS MONITOR';
    case 'network_monitor': return 'NETWORK MONITOR';
    case 'detection_engine': return 'DETECTION ENGINE';
    default: return (source || 'SYSTEM').toUpperCase();
  }
}

function mapEvent(event: any, index: number): SocEvent {
  const data = event?.data || {};
  const path = data.path || data.to || data.from;
  return {
    id: makeEventId(event, index),
    time: formatTime(event?.timestamp),
    source: getSourceLabel(event?.source) as any,
    event: event?.event_type || 'unknown_event',
    indicator: event?.indicator || '-',
    pid: event?.pid ?? undefined,
    process: event?.process || 'Unknown',
    sev: getSeverity(event) as any,
    path,
    entropy: data.entropy ?? undefined,
  } as SocEvent;
}

function mapNetwork(event: any, index: number): NetworkConnection {
  const data = event?.data || {};
  const remote = event?.remote_address || data.remote_address || '-';
  const local = event?.local_address || data.local_address || '-';
  const status = event?.status || data.status || 'UNKNOWN';
  const backendIndicator = String(event?.indicator || data.indicator || '').toLowerCase();
  const isRepeated = backendIndicator.includes('repeated_connection') || backendIndicator.includes('repeated_network');
  const isSuspicious = isRepeated || backendIndicator.includes('suspicious') || backendIndicator.includes('anomal');
  let indicator = 'NORMAL';
  if (isRepeated) indicator = 'repeated_connection_to_endpoint';
  else if (isSuspicious) indicator = backendIndicator || 'suspicious_network_activity';
  else if (backendIndicator) indicator = backendIndicator;
  return {
    id: `net-${makeEventId(event, index)}`,
    time: formatTime(event?.timestamp),
    process: event?.process || data.process || 'Unknown',
    pid: event?.pid ?? data.pid ?? 0,
    localAddress: local,
    remoteAddress: remote,
    status,
    indicator,
  };
}

function mapProcess(item: any): ProcessItem {
  const data = item?.data || {};
  return {
    pid: item?.pid ?? 0,
    name: item?.name || item?.process || 'Unknown',
    executablePath: data.exe || data.executable || 'Unavailable',
    user: data.username || 'Unknown',
    status: 'NORMAL',
    createTime: item?.timestamp || '--',
    threatScore: 0,
    parentProcess: 'Unavailable',
    userContext: data.username || 'Unknown',
    commandLine: 'Unavailable',
  } as ProcessItem;
}

function mapFile(item: any): FileActivityItem {
  const data = item?.data || {};
  const eventType = item?.event_type || 'unknown';
  let operation = eventType.replace('file_', '').toUpperCase();
  let threatLevel = 'normal';
  if (item?.source === 'detection_engine') threatLevel = 'critical';
  else if (eventType === 'file_deleted' || eventType === 'file_renamed') threatLevel = 'suspicious';
  return {
    id: `file-${Date.now()}-${Math.random()}`,
    time: formatTime(item?.timestamp),
    path: data.path || data.to || data.from || 'Unknown',
    operation,
    process: item?.process || 'Unknown',
    pid: item?.pid ?? 0,
    entropy: data.entropy ?? 0,
    threatLevel: threatLevel as any,
    isHoneytoken: Boolean(data.honeypot || data.honeytoken),
  } as FileActivityItem;
}

// ============================================================
// PROVIDER
// ============================================================

export const SocProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [events, setEvents] = useState<SocEvent[]>([]);
  const [connections, setConnections] = useState<NetworkConnection[]>([]);
  const [processes, setProcesses] = useState<ProcessItem[]>([]);
  const [selectedProcess, setSelectedProcess] = useState<ProcessItem | null>(null);
  const [fileActivities, setFileActivities] = useState<FileActivityItem[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activeIncident, setActiveIncident] = useState<Incident | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [actionLogs, setActionLogs] = useState<string[]>([]);
  const [currentTimeString, setCurrentTimeString] = useState<string>('--:--:-- IST');

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    threatState: 'normal',
    safeLabMode: true,
    hostIsolated: false,
    processSuspended: false,
    streamActive: true,
    eps: 0,
    activeProcessesCount: 0,
    suspiciousProcessesCount: 0,
    criticalAlertsCount: 0,
    confidence: 0,
    uptimeSeconds: 0,
  });

  const [behavioralTelemetry, setBehavioralTelemetry] = useState<BehavioralTelemetry>({
    filesCreated: 0,
    filesModified: 0,
    filesDeleted: 0,
    filesRenamed: 0,
    networkConns: 0,
    entropyAvg: 0,
  });

  // ----------------------------------------------------------
  // ACTION LOG HELPER
  // ----------------------------------------------------------
  const addLog = useCallback((msg: string) => {
    const now = new Date().toISOString().substring(11, 19);
    setActionLogs(prev => [`[${now}] ${msg}`, ...prev].slice(0, 100));
  }, []);

  // ----------------------------------------------------------
  // FETCH EVENTS
  // ----------------------------------------------------------
  const fetchEvents = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/events`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const rawEvents = Array.isArray(data.recent_events) ? data.recent_events : [];
      setEvents(rawEvents.map((e: any, i: number) => mapEvent(e, i)));
      const rawNetwork = Array.isArray(data.network_events_list) ? data.network_events_list : [];
      setConnections(rawNetwork.map((e: any, i: number) => mapNetwork(e, i)));
      const rawFiles = Array.isArray(data.file_events_list) ? data.file_events_list : [];
      setFileActivities(rawFiles.map((e: any) => mapFile(e)));

      const modifications = rawFiles.filter((e: any) => e.event_type === 'file_modified').length;
      const deletions = rawFiles.filter((e: any) => e.event_type === 'file_deleted').length;
      const renames = rawFiles.filter((e: any) => e.event_type === 'file_renamed').length;
      const creations = rawFiles.filter((e: any) => e.event_type === 'file_created').length;

      setBehavioralTelemetry({
        filesCreated: creations,
        filesModified: modifications,
        filesDeleted: deletions,
        filesRenamed: renames,
        networkConns: Number(data.network_events || 0),
        entropyAvg: 0,
      });

      setSystemStatus(prev => ({
        ...prev,
        criticalAlertsCount: Number(data.alerts || 0),
        eps: data.total_events || 0,
      }));
    } catch (error) {
      console.error('SOC events API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // FETCH STATUS
  // ----------------------------------------------------------
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const riskLevel = String(data.risk_level || 'NORMAL').toLowerCase();
      setSystemStatus(prev => ({
        ...prev,
        threatState: riskLevel as any,
        safeLabMode: Boolean(data.safe_lab_mode ?? true),
        streamActive: Boolean(data.monitoring ?? true),
        activeProcessesCount: Number(data.process_event_count || 0),
        suspiciousProcessesCount: Number(data.detection_event_count || 0),
        criticalAlertsCount: Number(data.detection_event_count || 0),
        confidence: riskLevel === 'critical' ? (data.ml_probability || 0) * 100 : riskLevel === 'high' ? 85 : 0,
      }));
    } catch (error) {
      console.error('SOC status API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // FETCH PROCESSES
  // ----------------------------------------------------------
  const fetchProcesses = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/processes`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const rawProcesses = Array.isArray(data.processes) ? data.processes : [];
      const mapped = rawProcesses.map((item: any) => mapProcess(item));
      setProcesses(mapped);
      setSelectedProcess(prev => {
        if (!prev) return mapped[0] || null;
        return mapped.find((p: ProcessItem) => p.pid === prev.pid) || mapped[0] || null;
      });
    } catch (error) {
      console.error('SOC process API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // FETCH INCIDENTS
  // ----------------------------------------------------------
  const fetchIncidents = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/incidents`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      setIncidents(Array.isArray(data.incidents) ? data.incidents : []);
      if (data.active_incident_id) {
        const active = (data.incidents || []).find(
          (i: Incident) => i.incident_id === data.active_incident_id
        );
        setActiveIncident(active || null);
      } else {
        setActiveIncident(null);
      }
    } catch (error) {
      console.error('SOC incidents API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // FETCH AUDIT
  // ----------------------------------------------------------
  const fetchAudit = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/audit`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      setAuditLog(Array.isArray(data.entries) ? data.entries : []);
    } catch (error) {
      console.error('SOC audit API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // FETCH HEALTH
  // ----------------------------------------------------------
  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('SOC health API error:', error);
    }
  }, []);

  // ----------------------------------------------------------
  // POLLING
  // ----------------------------------------------------------
  useEffect(() => {
    fetchEvents();
    fetchStatus();
    fetchProcesses();
    fetchIncidents();
    fetchAudit();
    fetchHealth();
    if (!systemStatus.streamActive) return;
    const interval = window.setInterval(() => {
      fetchEvents();
      fetchStatus();
      fetchProcesses();
      fetchIncidents();
      fetchAudit();
      fetchHealth();
    }, 2500);
    return () => window.clearInterval(interval);
  }, [fetchEvents, fetchStatus, fetchProcesses, fetchIncidents, fetchAudit, fetchHealth, systemStatus.streamActive]);

  // ----------------------------------------------------------
  // CLOCK
  // ----------------------------------------------------------
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const istTime = now.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
      });
      setCurrentTimeString(`${istTime} IST`);
    };
    updateTime();
    const interval = window.setInterval(updateTime, 1000);
    return () => window.clearInterval(interval);
  }, []);

  // ==========================================================
  // BACKEND ACTIONS
  // ==========================================================

  const postAPI = useCallback(async (url: string, body?: any): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      return await response.json();
    } catch (error) {
      addLog(`API ERROR: ${url} — ${error}`);
      return { success: false, message: String(error) };
    }
  }, [addLog]);

  const triggerContainment = useCallback(async () => {
    if (!activeIncident) {
      addLog('[DRY-RUN] No active incident for containment.');
      return;
    }
    addLog('[DRY-RUN] Triggering safe containment...');
    const result = await postAPI(`/api/incidents/${activeIncident.incident_id}/contain`);
    addLog(result.message || 'Containment completed.');
    setSystemStatus(prev => ({ ...prev, hostIsolated: true }));
    fetchIncidents();
    fetchAudit();
  }, [activeIncident, postAPI, addLog, fetchIncidents, fetchAudit]);

  const restoreHost = useCallback(async () => {
    addLog('[DRY-RUN] Restoring lab files...');
    const result = await postAPI('/api/recovery/restore');
    addLog(result.message || 'Restore completed.');
    setSystemStatus(prev => ({ ...prev, hostIsolated: false }));
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const killProcess = useCallback(async (pid: number) => {
    addLog(`[DRY-RUN] Simulating process isolation for PID ${pid}...`);
    const result = await postAPI('/api/prevention/isolate-process', { pid });
    addLog(result.message || 'Process isolation simulated.');
    fetchAudit();
  }, [postAPI, addLog, fetchAudit]);

  const toggleSafeLabMode = useCallback(() => {
    setSystemStatus(prev => {
      const next = !prev.safeLabMode;
      addLog(`Safe Lab Mode changed to: ${next ? 'ENABLED' : 'DISABLED'}`);
      return { ...prev, safeLabMode: next };
    });
  }, [addLog]);

  const simulateAttack = useCallback(async () => {
    addLog('Starting safe ransomware simulation...');
    const result = await postAPI('/api/simulation/run');
    addLog(result.message || 'Simulation finished.');
    fetchEvents();
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchEvents, fetchIncidents, fetchAudit]);

  const resetSimulation = useCallback(() => {
    addLog('UI state refreshed.');
    fetchEvents();
    fetchStatus();
    fetchProcesses();
    fetchIncidents();
    fetchAudit();
    fetchHealth();
  }, [fetchEvents, fetchStatus, fetchProcesses, fetchIncidents, fetchAudit, fetchHealth, addLog]);

  const acknowledgeIncident = useCallback(async (id: string) => {
    addLog(`Acknowledging incident ${id}...`);
    const result = await postAPI(`/api/incidents/${id}/acknowledge`);
    addLog(result.success ? 'Incident acknowledged → INVESTIGATING' : (result.error || 'Failed'));
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const containIncident = useCallback(async (id: string) => {
    addLog(`Containing incident ${id}...`);
    const result = await postAPI(`/api/incidents/${id}/contain`);
    addLog(result.message || 'Containment completed.');
    setSystemStatus(prev => ({ ...prev, hostIsolated: true }));
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const resolveIncident = useCallback(async (id: string) => {
    addLog(`Resolving incident ${id}...`);
    const result = await postAPI(`/api/incidents/${id}/resolve`);
    addLog(result.success ? 'Incident resolved.' : (result.error || 'Failed'));
    setSystemStatus(prev => ({ ...prev, hostIsolated: false }));
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const closeIncident = useCallback(async (id: string) => {
    addLog(`Closing incident ${id}...`);
    const result = await postAPI(`/api/incidents/${id}/close`);
    addLog(result.success ? 'Incident closed.' : (result.error || 'Failed'));
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const protectLabFiles = useCallback(async () => {
    addLog('Protecting lab files (creating snapshot)...');
    const result = await postAPI('/api/prevention/protect');
    addLog(result.message || 'Protection completed.');
    fetchAudit();
  }, [postAPI, addLog, fetchAudit]);

  const isolateProcess = useCallback(async (pid?: number, process?: string) => {
    addLog(`Simulating process isolation (PID=${pid || 'N/A'})...`);
    const result = await postAPI('/api/prevention/isolate-process', { pid, process });
    addLog(result.message || 'Process isolation simulated.');
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  const isolateNetwork = useCallback(async () => {
    addLog('Simulating network isolation...');
    const result = await postAPI('/api/prevention/isolate-network');
    addLog(result.message || 'Network isolation simulated.');
    fetchAudit();
  }, [postAPI, addLog, fetchAudit]);

  const createSnapshot = useCallback(async () => {
    addLog('Creating recovery snapshot...');
    const result = await postAPI('/api/recovery/snapshot');
    addLog(result.message || 'Snapshot created.');
    fetchAudit();
  }, [postAPI, addLog, fetchAudit]);

  const restoreLabFiles = useCallback(async () => {
    addLog('Restoring lab files from snapshot...');
    const result = await postAPI('/api/recovery/restore');
    addLog(result.message || 'Restore completed.');
    fetchIncidents();
    fetchAudit();
  }, [postAPI, addLog, fetchIncidents, fetchAudit]);

  // ----------------------------------------------------------
  // SIMPLE UI ACTIONS
  // ----------------------------------------------------------
  const addEvent = useCallback((event: Omit<SocEvent, 'id'>) => {
    const newEvent = { ...event, id: `ui-${Date.now()}` } as SocEvent;
    setEvents(prev => [newEvent, ...prev]);
  }, []);

  const clearEvents = useCallback(() => { setEvents([]); }, []);
  const toggleStream = useCallback(() => {
    setSystemStatus(prev => ({ ...prev, streamActive: !prev.streamActive }));
  }, []);

  // ==========================================================
  // PROVIDER
  // ==========================================================
  return (
    <SocContext.Provider value={{
      activeTab, setActiveTab,
      systemStatus, setSystemStatus,
      events, addEvent, clearEvents, toggleStream,
      connections, processes, selectedProcess, setSelectedProcess,
      fileActivities, behavioralTelemetry, actionLogs, currentTimeString,
      incidents, activeIncident, auditLog, systemHealth,
      triggerContainment, restoreHost, killProcess, toggleSafeLabMode,
      simulateAttack, resetSimulation,
      acknowledgeIncident, containIncident, resolveIncident, closeIncident,
      protectLabFiles, isolateProcess, isolateNetwork,
      createSnapshot, restoreLabFiles,
    }}>
      {children}
    </SocContext.Provider>
  );
};

// ============================================================
// HOOK
// ============================================================
export const useSoc = () => {
  const context = useContext(SocContext);
  if (!context) throw new Error('useSoc must be used within a SocProvider');
  return context;
};
