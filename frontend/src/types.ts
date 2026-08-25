export type TabType =
  | 'overview'
  | 'live-events'
  | 'file-activity'
  | 'network-activity'
  | 'process-activity'
  | 'detection-risk'
  | 'response'
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
  status: 'ESTAB' | 'SYN_SENT' | 'LISTEN' | 'TIME_WAIT' | 'CLOSE_WAIT';
  indicator: 'NORMAL' | 'SUSPICIOUS' | 'ANOMALY';
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
  threatState: 'normal' | 'elevated' | 'critical';
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
