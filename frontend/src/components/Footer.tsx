import React from 'react';
import { ShieldAlert, ExternalLink, GitBranch, Terminal } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-20 border-t border-[var(--border-subtle)] bg-[#07090e] py-12 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        
        {/* Left Column */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20">
            <ShieldAlert size={18} className="text-rose-500" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-200">AI Production Incident Response Platform</h4>
            <p className="text-xs text-slate-500">Autonomous 5-Agent Investigation Engine powered by OpenAI Agents SDK & MCP</p>
          </div>
        </div>

        {/* Center Info Badges */}
        <div className="flex items-center gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Terminal size={14} className="text-blue-400" />
            Python 3.12 + FastAPI
          </span>
          <span className="flex items-center gap-1.5">
            <GitBranch size={14} className="text-emerald-400" />
            82/82 Tests Passed
          </span>
        </div>

        {/* Right Links */}
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <a 
            href="https://github.com/MuneebMalik244535/AI-Production-Incident-Response" 
            target="_blank" 
            rel="noreferrer"
            className="hover:text-blue-400 transition-colors flex items-center gap-1"
          >
            Repository <ExternalLink size={12} />
          </a>
          <span>&bull;</span>
          <span>MIT License</span>
        </div>

      </div>
    </footer>
  );
};
