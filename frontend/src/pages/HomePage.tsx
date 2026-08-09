import React from 'react';
import { 
  ArrowRight, 
  CheckCircle2, 
  Terminal, 
  Zap,
  AlertTriangle
} from 'lucide-react';

interface HomePageProps {
  onGoToDashboard: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onGoToDashboard }) => {
  return (
    <div className="space-y-24 max-w-7xl mx-auto px-6 pt-8 pb-16">
      
      {/* ── HERO SECTION ────────────────────────────────────────────────── */}
      <section className="relative text-center space-y-8 pt-12 pb-6">
        <div className="gradient-hero-glow" />

        {/* Badge Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-400">
          <Zap size={14} className="text-blue-400" />
          <span>Autonomous AI Production Engineering System</span>
        </div>

        {/* Hero Headline */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-100 max-w-4xl mx-auto leading-tight">
          When Production Breaks at 3 AM, <br />
          <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
            AI Agents Investigate & Propose Fixes
          </span>
        </h1>

        {/* Subhead */}
        <p className="text-base md:text-lg text-slate-400 max-w-2xl mx-auto font-medium leading-relaxed">
          Replaces the manual 45-minute outage triage process with 5 specialized AI agents working via Model Context Protocol (MCP) to deliver root cause analysis and GitHub PR fixes in under 2 minutes.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <button
            onClick={onGoToDashboard}
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-xl shadow-blue-500/25 transition-all transform hover:-translate-y-0.5"
          >
            <span>Launch Live Operations Center</span>
            <ArrowRight size={16} />
          </button>
          
          <a
            href="https://github.com/MuneebMalik244535/AI-Production-Incident-Response"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 font-semibold text-sm border border-slate-700/50 transition-all"
          >
            <Terminal size={16} className="text-slate-400" />
            <span>Explore Architecture Code</span>
          </a>
        </div>

        {/* Key Metrics Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-10">
          <div className="glass-card p-5 text-center">
            <div className="text-2xl md:text-3xl font-black text-emerald-400 font-mono">2 Mins</div>
            <div className="text-xs text-slate-400 font-medium mt-1">Mean Time to Resolution (MTTR)</div>
          </div>
          <div className="glass-card p-5 text-center">
            <div className="text-2xl md:text-3xl font-black text-blue-400 font-mono">5 Agents</div>
            <div className="text-xs text-slate-400 font-medium mt-1">OpenAI Agents SDK Pipeline</div>
          </div>
          <div className="glass-card p-5 text-center">
            <div className="text-2xl md:text-3xl font-black text-cyan-300 font-mono">82 / 82</div>
            <div className="text-xs text-slate-400 font-medium mt-1">Passing Unit & E2E Tests</div>
          </div>
          <div className="glass-card p-5 text-center">
            <div className="text-2xl md:text-3xl font-black text-purple-400 font-mono">100%</div>
            <div className="text-xs text-slate-400 font-medium mt-1">Human-in-the-Loop Safe</div>
          </div>
        </div>
      </section>

      {/* ── PROBLEM VS SOLUTION ─────────────────────────────────────────── */}
      <section className="space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100">
            Why Traditional Incident Response is Broken
          </h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            Traditional incident response relies on sleepy engineers digging through disconnected logs and git commits at 3 AM.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          
          {/* Traditional Way */}
          <div className="glass-card p-8 space-y-6 border-rose-500/20 bg-rose-950/10">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertTriangle size={24} />
              <h3 className="text-lg font-bold">Traditional Incident Response</h3>
            </div>
            
            <ul className="space-y-4 text-sm text-slate-300">
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">&times;</span>
                <span>Engineer wakes up to PagerDuty alert at 3 AM and spends 20 minutes finding logs.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">&times;</span>
                <span>Manually searches GitHub recent commits and deployment logs to find suspicious code.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">&times;</span>
                <span>High human error risk while applying emergency hotfixes under outage stress.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">&times;</span>
                <span><strong>45 to 90 minutes</strong> total downtime per production incident.</span>
              </li>
            </ul>
          </div>

          {/* Autonomous AI Way */}
          <div className="glass-card p-8 space-y-6 border-emerald-500/20 bg-emerald-950/10">
            <div className="flex items-center gap-3 text-emerald-400">
              <CheckCircle2 size={24} />
              <h3 className="text-lg font-bold">Our Autonomous AI Platform</h3>
            </div>
            
            <ul className="space-y-4 text-sm text-slate-300">
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">&#10003;</span>
                <span>Automated anomaly detector spots error spikes instantly and triggers the agent pipeline.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">&#10003;</span>
                <span>Log Agent & GitHub Agent correlate log traces with code commit diffs using MCP tools.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">&#10003;</span>
                <span>Root Cause Agent calculates 91% confidence score and drafts a complete GitHub PR fix.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 font-bold">&#10003;</span>
                <span><strong>Under 2 minutes</strong> total time with 1-click human approval safety.</span>
              </li>
            </ul>
          </div>

        </div>
      </section>

      {/* ── 4-STEP AUTOMATION PIPELINE ──────────────────────────────────── */}
      <section className="space-y-12">
        <div className="text-center space-y-3">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-100">
            How The AI Pipeline Resolves Outages
          </h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            From error spike detection to GitHub PR creation in 4 automated steps.
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-6">
          <div className="glass-card p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-sm">1</div>
            <h4 className="font-bold text-slate-200">Anomaly Detection</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Log streams are monitored for 500 spikes or database pool timeout errors.
            </p>
          </div>

          <div className="glass-card p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm">2</div>
            <h4 className="font-bold text-slate-200">MCP Tool Investigation</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Log MCP Server & GitHub MCP Server query traces and commit diffs in parallel.
            </p>
          </div>

          <div className="glass-card p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-sm">3</div>
            <h4 className="font-bold text-slate-200">Root Cause Synthesis</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Root Cause Agent computes confidence score and evidence correlation timeline.
            </p>
          </div>

          <div className="glass-card p-6 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-sm">4</div>
            <h4 className="font-bold text-slate-200">1-Click PR Remediation</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Human engineer approves fix and system automatically opens GitHub PR & posts Slack alert.
            </p>
          </div>
        </div>
      </section>

      {/* ── CALL TO ACTION ──────────────────────────────────────────────── */}
      <section className="glass-card p-12 text-center space-y-6 border-blue-500/30 bg-gradient-to-b from-blue-950/20 to-transparent">
        <h2 className="text-2xl md:text-3xl font-extrabold text-slate-100">
          Ready to Experience Autonomous Incident Response?
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Explore the interactive Live Operations Center or run failure simulations in real-time.
        </p>
        <button
          onClick={onGoToDashboard}
          className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-xl shadow-blue-500/25 transition-all"
        >
          <span>Open Live Operations Dashboard</span>
          <ArrowRight size={16} />
        </button>
      </section>

    </div>
  );
};
