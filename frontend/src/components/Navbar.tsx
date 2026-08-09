import React from 'react';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Cpu, 
  BookOpen, 
  Home, 
  ExternalLink,
  Server
} from 'lucide-react';

interface NavbarProps {
  activeTab: 'home' | 'dashboard' | 'architecture' | 'docs';
  setActiveTab: (tab: 'home' | 'dashboard' | 'architecture' | 'docs') => void;
  isLiveConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isLiveConnected }) => {
  const navItems = [
    { id: 'home', label: 'Overview', icon: Home },
    { id: 'dashboard', label: 'Live Operations', icon: LayoutDashboard },
    { id: 'architecture', label: 'Architecture & Tests', icon: Cpu },
    { id: 'docs', label: 'Docs & Integrations', icon: BookOpen },
  ] as const;

  return (
    <header className="sticky top-0 z-50 px-6 py-4 backdrop-blur-xl bg-[#07090e]/80 border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Logo & Title */}
        <div 
          onClick={() => setActiveTab('home')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 group-hover:border-rose-500/40 transition-all">
            <ShieldAlert size={22} className="text-rose-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-slate-100">AI Incident Response</h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Autonomous Multi-Agent Incident Platform</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 p-1.5 rounded-2xl bg-[#0e131f] border border-[var(--border-subtle)]">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isActive 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Status Indicator & Repository Link */}
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
            isLiveConnected 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
              : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
          }`}>
            <Server size={13} />
            <span>{isLiveConnected ? 'FastAPI Live' : 'Demo Mode'}</span>
          </div>

          <a
            href="https://github.com/MuneebMalik244535/AI-Production-Incident-Response"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/50 transition-all"
          >
            <span>GitHub</span>
            <ExternalLink size={13} className="text-slate-400" />
          </a>
        </div>

      </div>
    </header>
  );
};
