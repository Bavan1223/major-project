import React from 'react';
import { useSoc } from '../context/SocContext';
import { TabType } from '../types';
import {
  LayoutDashboard,
  Zap,
  FolderOpen,
  Network,
  Terminal,
  AlertTriangle,
  ShieldCheck,
  Activity,
  Shield,
} from 'lucide-react';

interface NavItem {
  id: TabType;
  label: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
  badge?: string | number;
  badgeColor?: string;
}

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, systemStatus } = useSoc();

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    {
      id: 'live-events',
      label: 'Live Events',
      icon: Zap,
      badge: systemStatus.streamActive ? 'LIVE' : 'PAUSED',
      badgeColor: systemStatus.streamActive ? 'bg-[#00a572]/20 text-[#4edea3]' : 'bg-[#424754] text-[#c2c6d6]',
    },
    { id: 'file-activity', label: 'File Activity', icon: FolderOpen },
    { id: 'network-activity', label: 'Network Activity', icon: Network },
    {
      id: 'process-activity',
      label: 'Process Activity',
      icon: Terminal,
      badge: systemStatus.suspiciousProcessesCount > 0 ? systemStatus.suspiciousProcessesCount : undefined,
      badgeColor: 'bg-[#ffb4ab]/20 text-[#ffb4ab]',
    },
    {
      id: 'detection-risk',
      label: 'Detection & Risk',
      icon: AlertTriangle,
      badge: systemStatus.criticalAlertsCount > 0 ? systemStatus.criticalAlertsCount : undefined,
      badgeColor: 'bg-[#93000a] text-[#ffdad6]',
    },
    { id: 'response', label: 'Response', icon: ShieldCheck },
    { id: 'prevention', label: 'Prevention', icon: Shield },
    { id: 'system-health', label: 'System Health', icon: Activity },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#0b0e15] border-r border-[#424754] z-50 flex flex-col select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#424754] mb-2">
        <div className="flex items-center gap-1.5 text-[#adc6ff] mb-1">
          <Shield className="w-5 h-5 text-[#adc6ff]" />
          <span className="font-mono text-[10px] font-bold tracking-widest text-[#adc6ff]">
            SYSTEM CORE
          </span>
        </div>
        <div className="text-[18px] font-semibold tracking-tighter text-[#e1e2ec] flex items-center justify-between">
          <span>RD // SOC</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1d2027] text-[#8c909f] border border-[#424754]">
            v2.4
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-1 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-4 py-2.5 transition-all text-left group ${
                isActive
                  ? 'bg-[#32353c] text-[#adc6ff] border-l-2 border-[#adc6ff] font-medium'
                  : 'text-[#c2c6d6] hover:bg-[#272a31] hover:text-[#e1e2ec] border-l-2 border-transparent'
              }`}
            >
              <div className="flex items-center">
                <Icon
                  size={18}
                  className={`mr-3 transition-colors ${
                    isActive ? 'text-[#adc6ff]' : 'text-[#8c909f] group-hover:text-[#e1e2ec]'
                  }`}
                />
                <span className="text-[14px]">{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span
                  className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border border-current/20 ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Status Panel Footer */}
      <div className="p-4 bg-[#191b23] border-t border-[#424754] space-y-2">
        <div className="flex items-center justify-between font-mono text-[11px] text-[#c2c6d6]">
          <span>ML Model</span>
          <span className="text-[#4edea3] font-medium flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
            ONLINE v2.0.0
          </span>
        </div>
        <div className="flex items-center justify-between font-mono text-[11px] text-[#c2c6d6]">
          <span>Backend</span>
          <span className="text-[#4edea3] font-medium flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3]" />
            CONNECTED
          </span>
        </div>
      </div>
    </aside>
  );
};
