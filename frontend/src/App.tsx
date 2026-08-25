import React from 'react';
import { SocProvider, useSoc } from './context/SocContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { OverviewView } from './components/views/OverviewView';
import { LiveEventsView } from './components/views/LiveEventsView';
import { NetworkActivityView } from './components/views/NetworkActivityView';
import { ProcessActivityView } from './components/views/ProcessActivityView';
import { DetectionRiskView } from './components/views/DetectionRiskView';
import { FileActivityView } from './components/views/FileActivityView';
import { ResponseView } from './components/views/ResponseView';
import { PreventionView } from './components/views/PreventionView';
import { SystemHealthView } from './components/views/SystemHealthView';

const MainContent: React.FC = () => {
  const { activeTab } = useSoc();

  return (
    <main className="ml-64 mt-16 min-h-[calc(100vh-64px)] bg-[#10131a]">
      {activeTab === 'overview' && <OverviewView />}
      {activeTab === 'live-events' && <LiveEventsView />}
      {activeTab === 'file-activity' && <FileActivityView />}
      {activeTab === 'network-activity' && <NetworkActivityView />}
      {activeTab === 'process-activity' && <ProcessActivityView />}
      {activeTab === 'detection-risk' && <DetectionRiskView />}
      {activeTab === 'response' && <ResponseView />}
      {activeTab === 'prevention' && <PreventionView />}
      {activeTab === 'system-health' && <SystemHealthView />}
    </main>
  );
};

export default function App() {
  return (
    <SocProvider>
      <div className="min-h-screen bg-[#10131a] text-[#e1e2ec] font-sans antialiased">
        <Sidebar />
        <Header />
        <MainContent />
      </div>
    </SocProvider>
  );
}
