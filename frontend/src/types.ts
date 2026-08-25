export type TabType =
  | 'overview'
  | 'live-events'
  | 'file-activity'
  | 'network-activity'
  | 'process-activity'
  | 'detection-risk'
  | 'response'
  | 'prevention'
  | 'system-health';

export type SeverityType = 'info' | 'low' | 'medium' | 'high' | 'critical';

export type SourceType =
  | 'DETECTION ENGINE'
  | 'FILE MONITOR'
  | 'NETWORK MONITOR'
  | 'PROCESS MONITOR'
  | 'EVENT COLLECTOR';

export interface SocEvent {
  id: string;
  time: string;
  source: SourceType;
  event: string;
  indicator: string;
  pid: number;
  process: string;
  sev: SeverityType;
  entropy?: number;
  details?: string;
  path?: string;
}

export interface NetworkConnection {
  id: string;
  time: string;
  process: string;
  pid: number;
  localAddress: string;
  remoteAddress: string;
  status: string;
  indicator: string;
}

export interface ProcessItem {
  pid: number;
  name: string;
  executablePath: string;
  user: string;
  status: 'NORMAL' | 'SUSPICIOUS' | 'ANOMALOUS' | 'TERMINATED';
  createTime: string;
  threatScore?: number;
  parentProcess?: string;
  userContext?: string;
  commandLine?: string;
  timeline?: {
    time: string;
    description: string;
    matchedRule?: string;
    type: 'created' | 'handle' | 'critical' | 'terminated';
  }[];
}

export interface FileActivityItem {
  id: string;
  time: string;
  path: string;
  operation: 'CREATED' | 'MODIFIED' | 'RENAMED' | 'DELETED' | 'ENCRYPTED';
  process: string;
  pid: number;
  entropy: number;
  isHoneytoken?: boolean;
  threatLevel: 'normal' | 'suspicious' | 'critical';
}

export interface BehavioralTelemetry {
  filesCreated: number;
  filesModified: number;
  filesDeleted: number;
  filesRenamed: number;
  networkConns: number;
  entropyAvg: number;
}

export interface SystemStatus {
  threatState: 'normal' | 'elevated' | 'critical' | 'high' | 'medium' | 'low';
  safeLabMode: boolean;
  hostIsolated: boolean;
  processSuspended: boolean;
  streamActive: boolean;
  eps: number;
  activeProcessesCount: number;
  suspiciousProcessesCount: number;
  criticalAlertsCount: number;
  confidence: number;
  uptimeSeconds: number;
}

// ==============================================================
// INCIDENT TYPES
// ==============================================================

export type IncidentStatus =
  | 'OPEN'
  | 'INVESTIGATING'
  | 'CONTAINED'
  | 'RESOLVED'
  | 'CLOSED';

export interface IncidentTimeline {
  timestamp: string;
  action: string;
  detail: string;
}

export interface Incident {
  incident_id: string;
  created_at: string;
  updated_at: string;
  status: IncidentStatus;
  risk_level: string;
  reason: string;
  signals: string[];
  confidence: number;
  ml_probability: number;
  ml_contributed: boolean;
  process: string | null;
  pid: number | null;
  file_count: number;
  network_count: number;
  affected_paths: string[];
  remote_endpoints: string[];
  response_action: string;
  protection_action: string;
  containment_status: string;
  recovery_status: string;
  timeline: IncidentTimeline[];
}

// ==============================================================
// AUDIT TYPES
// ==============================================================

export interface AuditEntry {
  timestamp: string;
  actor: string;
  action: string;
  incident_id: string | null;
  mode: string;
  success: boolean;
  detail: string;
}

// ==============================================================
// HEALTH TYPES
// ==============================================================

export interface SystemHealth {
  backend: string;
  file_monitor: string;
  process_monitor: string;
  network_monitor: string;
  detection_pipeline: string;
  event_log: string;
  ml_model: string;
  safe_lab_mode: boolean;
  protection_mode: string;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  uptime_seconds: number;
}
