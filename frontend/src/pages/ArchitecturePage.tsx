import React from 'react';
import { 
  Bot, 
  CheckCircle2, 
  Cpu, 
  Layers
} from 'lucide-react';

export const ArchitecturePage: React.FC = () => {
  const agentDetails = [
    {
      name: 'Incident Commander',
      role: 'Pipeline Orchestrator',
      model: 'GPT-4o / Handoffs',
      tools: 'Handoffs to Log, GitHub, Root Cause & Recommendation agents',
      description: 'Receives production alerts, determines investigation strategy based on severity, and coordinates specialist agent handoffs.',
      iconColor: 'text-purple-400'
    },
    {
      name: 'Log Analysis Agent',
      role: 'Log Forensic Investigator',
      model: 'GPT-4o + MCP',
      tools: 'Log MCP Server (search_logs, get_error_summary)',
      description: 'Queries application log stores, analyzes error frequency, identifies stack traces, and detects anomaly spikes.',
      iconColor: 'text-blue-400'
    },
    {
      name: 'GitHub Investigation Agent',
      role: 'Code Forensic Investigator',
      model: 'GPT-4o + MCP',
      tools: 'GitHub MCP Server (search_commits, get_commit, search_code)',
      description: 'Searches recent commits, inspects file diff patches, checks author info, and correlates code changes with incident timestamps.',
      iconColor: 'text-cyan-400'
    },
    {
      name: 'Root Cause Agent',
      role: 'Causal Reasoning Specialist',
      model: 'GPT-4o Reasoner',
      tools: 'Structured Evidence Synthesizer',
      description: 'Correlates log traces with suspicious commit diffs to deduce exact root cause and calculate AI confidence score (e.g. 91%).',
      iconColor: 'text-rose-400'
    },
    {
      name: 'Recommendation Agent',
      role: 'SRE Remediation Expert',
      model: 'GPT-4o Generator',
      tools: 'GitHub PR Description Generator',
      description: 'Generates 4 prioritized fix steps, assesses risk level (CRITICAL), and drafts ready-to-merge GitHub PR descriptions.',
      iconColor: 'text-emerald-400'
    }
  ];

  const testSuiteBreakdown = [
    { module: 'test_config.py', tests: 6, focus: 'Settings singleton, defaults & DB URL validation' },
    { module: 'test_health.py', tests: 3, focus: 'Health check endpoint, semver format & status' },
    { module: 'test_incidents.py', tests: 22, focus: 'Incidents CRUD & approval state machine guards' },
    { module: 'test_schemas.py', tests: 18, focus: 'Pydantic models, enums & confidence bounds' },
    { module: 'test_mcp_servers.py', tests: 11, focus: 'Log MCP Server & GitHub MCP Server tool execution' },
    { module: 'test_agents_pipeline.py', tests: 6, focus: 'OpenAI Agents SDK 5-Agent pipeline & Runner.run' },
    { module: 'test_db.py', tests: 5, focus: 'Async SQLAlchemy ORM models & DB repositories' },
    { module: 'test_payment_simulation.py', tests: 7, focus: 'Payment Service failure injection & anomaly detector' },
    { module: 'test_production_features.py', tests: 4, focus: 'Slack Webhooks & GitHub PR creation integrations' },
  ];

  const phaseRoadmap = [
    { phase: 'Phase 1', name: 'FastAPI Backend Skeleton & Schemas', status: 'Completed', tests: '49 Tests' },
    { phase: 'Phase 2', name: 'MCP Tool Servers (Log & GitHub FastMCP)', status: 'Completed', tests: '60 Tests' },
    { phase: 'Phase 3', name: 'OpenAI Agents SDK 5-Agent Pipeline', status: 'Completed', tests: '66 Tests' },
    { phase: 'Phase 4', name: 'Async SQLAlchemy Database Persistence', status: 'Completed', tests: '71 Tests' },
    { phase: 'Phase 5', name: 'Real Failure Simulation (Payment Service)', status: 'Completed', tests: '78 Tests' },
    { phase: 'Phase 6', name: 'Production Hardening (Auth, Slack, GitHub PR, Docker)', status: 'Completed', tests: '82 Tests' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-16">
      
      {/* Page Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs font-semibold text-cyan-400">
          <Cpu size={14} />
          <span>System Architecture & Verification Bench</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-extrabold text-slate-100 tracking-tight">
          How We Built It & Verified Every Component
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Comprehensive breakdown of our 5 specialized AI agents, Model Context Protocol (MCP) servers, and 82/82 passing unit and integration tests.
        </p>
      </div>

      {/* ── TEST METRICS HEADER STRIP ───────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-6 text-center space-y-1">
          <div className="text-3xl font-black text-emerald-400 font-mono">82 / 82</div>
          <div className="text-xs text-slate-400 font-medium">Total Tests Passed (100%)</div>
        </div>
        <div className="glass-card p-6 text-center space-y-1">
          <div className="text-3xl font-black text-blue-400 font-mono">5 Agents</div>
          <div className="text-xs text-slate-400 font-medium">Specialized OpenAI SDK Pipeline</div>
        </div>
        <div className="glass-card p-6 text-center space-y-1">
          <div className="text-3xl font-black text-cyan-300 font-mono">2 MCP Servers</div>
          <div className="text-xs text-slate-400 font-medium">FastMCP Log & GitHub Servers</div>
        </div>
        <div className="glass-card p-6 text-center space-y-1">
          <div className="text-3xl font-black text-purple-400 font-mono">16.87s</div>
          <div className="text-xs text-slate-400 font-medium">Total Test Execution Time</div>
        </div>
      </div>

      {/* ── 5 AGENTS BREAKDOWN SECTION ──────────────────────────────────── */}
      <div className="space-y-8">
        <div className="flex items-center gap-3">
          <Bot size={24} className="text-purple-400" />
          <h2 className="text-2xl font-bold text-slate-100">The 5 Specialized AI Agents</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {agentDetails.map((agent, idx) => (
            <div key={idx} className="glass-card p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/50">
                    <Bot size={20} className={agent.iconColor} />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-100">{agent.name}</h3>
                    <span className="text-xs text-slate-400 font-medium">{agent.role}</span>
                  </div>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {agent.model}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {agent.description}
              </p>

              <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 font-mono">
                <strong className="text-slate-300">Tools:</strong> {agent.tools}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── TEST SUITE REPORT TABLE ─────────────────────────────────────── */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <CheckCircle2 size={24} className="text-emerald-400" />
          <h2 className="text-2xl font-bold text-slate-100">Complete Pytest Test Suite Report (82 Tests)</h2>
        </div>

        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-[var(--border-subtle)] text-slate-400 uppercase text-[10px] font-bold">
                <tr>
                  <th className="py-3.5 px-6">Test File Module</th>
                  <th className="py-3.5 px-6">Test Count</th>
                  <th className="py-3.5 px-6">Verification Target</th>
                  <th className="py-3.5 px-6">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)] text-slate-300 font-medium">
                {testSuiteBreakdown.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-6 font-mono text-cyan-300">{row.module}</td>
                    <td className="py-3.5 px-6 font-bold">{row.tests} tests</td>
                    <td className="py-3.5 px-6 text-slate-400">{row.focus}</td>
                    <td className="py-3.5 px-6">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full badge-success font-bold text-[10px]">
                        <CheckCircle2 size={12} /> PASSED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── PHASE PROGRESSION ROADMAP ───────────────────────────────────── */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Layers size={24} className="text-blue-400" />
          <h2 className="text-2xl font-bold text-slate-100">6-Phase Build Execution Roadmap</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {phaseRoadmap.map((item, idx) => (
            <div key={idx} className="glass-card p-6 space-y-3 border-emerald-500/20">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-blue-400 font-mono">{item.phase}</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {item.status}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-100">{item.name}</h3>
              <p className="text-xs text-slate-400 font-mono">{item.tests}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
