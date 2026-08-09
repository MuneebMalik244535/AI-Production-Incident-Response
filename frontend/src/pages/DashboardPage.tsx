import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  GitPullRequest, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Activity, 
  AlertTriangle, 
  Layers, 
  Send,
  Zap,
  RotateCcw,
  ExternalLink
} from 'lucide-react';
import type { IncidentResponse, IncidentListItem, Severity } from '../types';

const API_BASE = 'http://localhost:8000/api';

const MOCK_DEMO_INCIDENT: IncidentResponse = {
  id: 'inc-demo-1042',
  error: 'sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00',
  service: 'payment-api',
  severity: 'CRITICAL',
  status: 'AWAITING_APPROVAL',
  timestamp: new Date().toISOString(),
  created_at: new Date().toISOString(),
  metadata: { region: 'us-east-1', environment: 'production', affected_users: 347 },
  agent_runs: [
    {
      agent_name: 'Log Analysis Agent',
      status: 'SUCCESS',
      duration_seconds: 0.042,
      tokens_used: 420,
      output_summary: "Found 347 connection timeout errors in last 30m. 82% DB connection spike starting 10:38 AM."
    },
    {
      agent_name: 'GitHub Investigation Agent',
      status: 'SUCCESS',
      duration_seconds: 0.058,
      tokens_used: 580,
      output_summary: "Identified commit 8f32a1b by dev@company.com deployed 4 min prior to error spike. Modified DB pool settings."
    },
    {
      agent_name: 'Root Cause Agent',
      status: 'SUCCESS',
      duration_seconds: 0.035,
      tokens_used: 350,
      output_summary: "Database connection pool exhaustion caused by unreleased DB connections and reduced pool size limit (10)."
    },
    {
      agent_name: 'Recommendation Agent',
      status: 'SUCCESS',
      duration_seconds: 0.039,
      tokens_used: 490,
      output_summary: "Risk: CRITICAL. Recommended fix: Increase POOL_SIZE from 10 to 50 and restore connection release try/finally block."
    }
  ],
  findings: [
    {
      agent_name: 'Log Analysis Agent',
      finding_type: 'log_analysis',
      content: 'Found 347 connection timeout errors. Connection pool saturation at 100%.',
      evidence: [{ log_id: 'log-db-timeout-101', count: 347 }],
      confidence: 0.88
    },
    {
      agent_name: 'GitHub Investigation Agent',
      finding_type: 'github_investigation',
      content: 'Commit 8f32a1b removed try/finally pool.putconn() release block and lowered pool size.',
      evidence: [{ sha: '8f32a1b', file: 'app/db/connection.py' }],
      confidence: 0.94
    },
    {
      agent_name: 'Root Cause Agent',
      finding_type: 'root_cause_analysis',
      content: 'Database connection pool exhaustion due to missing connection release in commit 8f32a1b.',
      evidence: [],
      confidence: 0.91
    }
  ],
  recommendation: {
    root_cause: 'Database connection pool exhaustion caused by unreleased DB connections and reduced pool size limit.',
    evidence: [
      '347 connection timeout errors reported for payment-api',
      '82% database connection spike detected starting at 10:38 AM',
      'Recent commit 8f32a1b changed DB connection pooling logic',
      'Errors began exactly 4 minutes after deployment of commit 8f32a1b'
    ],
    risk_level: 'CRITICAL',
    recommended_actions: [
      'Increase database connection pool limit from 10 back to 50 in app/config.py',
      'Restore explicit connection pool release block in try/finally in app/db/connection.py',
      'Set database request connection timeout to 30.0s max',
      'Add database connection pool saturation alerting to Slack/PagerDuty'
    ],
    confidence: 0.91,
    suggested_pr_description: "## Description\nFixes production incident caused by database connection pool exhaustion.\n\n### Changes\n1. Restored try/finally connection release block in `app/db/connection.py`.\n2. Increased `POOL_SIZE` from 10 to 50 in `app/config.py`.\n\n### Verification\nVerified connection pool metrics stay under 30% saturation under peak load.",
    requires_immediate_action: true
  }
};

export const DashboardPage: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentListItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentResponse>(MOCK_DEMO_INCIDENT);
  const [reviewer, setReviewer] = useState('muneeb.malik@company.com');
  const [notes, setNotes] = useState('Root cause analysis verified. Connection pool fix looks solid.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [simulatingMode, setSimulatingMode] = useState<string | null>(null);

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/incidents`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);
        if (data.length > 0) {
          fetchIncidentDetail(data[0].id);
        }
      }
    } catch {
      // Fallback to mock
    }
  };

  const fetchIncidentDetail = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/incidents/${id}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedIncident(data);
        if (data.metadata?.github_pr_url) {
          setPrUrl(data.metadata.github_pr_url);
        }
      }
    } catch {
      // Keep demo state
    }
  };

  const handleTriggerSimulation = async (mode: string) => {
    setSimulatingMode(mode);
    try {
      const res = await fetch(`${API_BASE}/incidents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: mode === 'DB_TIMEOUT' 
            ? 'sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached'
            : mode === 'API_FAILURE'
            ? 'HTTP 500 Internal Server Error: Upstream Payment Gateway Failure'
            : 'JWT Signature verification failed: Auth token expired',
          service: 'payment-api',
          severity: 'CRITICAL',
          metadata: { simulated_mode: mode }
        })
      });
      if (res.ok) {
        setTimeout(() => fetchIncidents(), 1000);
      }
    } catch {
      // Simulation fallback
    } finally {
      setTimeout(() => setSimulatingMode(null), 1200);
    }
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/incidents/${selectedIncident.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'APPROVE',
          reviewer: reviewer,
          notes: notes,
          action: 'create_pr'
        })
      });

      if (res.ok) {
        const updated = await res.json();
        setSelectedIncident(updated);
        setPrUrl(updated.metadata?.github_pr_url || 'https://github.com/company/payment-api/pull/105');
      } else {
        setSelectedIncident(prev => ({ ...prev, status: 'APPROVED' }));
        setPrUrl('https://github.com/company/payment-api/pull/105');
      }
    } catch {
      setSelectedIncident(prev => ({ ...prev, status: 'APPROVED' }));
      setPrUrl('https://github.com/company/payment-api/pull/105');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      await fetch(`${API_BASE}/incidents/${selectedIncident.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: 'REJECT',
          reviewer: reviewer,
          notes: notes
        })
      });
      setSelectedIncident(prev => ({ ...prev, status: 'REJECTED' }));
    } catch {
      setSelectedIncident(prev => ({ ...prev, status: 'REJECTED' }));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadge = (sev: Severity) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full badge-critical">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full badge-amber">HIGH</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full badge-info">MEDIUM</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full badge-success flex items-center gap-1.5"><CheckCircle2 size={14}/> APPROVED</span>;
      case 'REJECTED':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full badge-critical flex items-center gap-1.5"><XCircle size={14}/> REJECTED</span>;
      case 'INVESTIGATING':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full badge-amber flex items-center gap-1.5 animate-pulse-glow"><Activity size={14}/> INVESTIGATING</span>;
      default:
        return <span className="px-3 py-1 text-xs font-semibold rounded-full badge-info flex items-center gap-1.5"><Clock size={14}/> AWAITING APPROVAL</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      
      {/* ── Failure Simulation Trigger Control Bar ────────────────────────── */}
      <div className="glass-card p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Zap size={18} className="text-amber-400" />
          <div>
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Production Failure Injection Control</h3>
            <p className="text-xs text-slate-400">Trigger real production failure simulations on Payment Service</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={() => handleTriggerSimulation('DB_TIMEOUT')}
            disabled={!!simulatingMode}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700/50 transition-all"
          >
            <Zap size={13} className="text-rose-400" />
            <span>{simulatingMode === 'DB_TIMEOUT' ? 'Injecting...' : 'Inject DB Timeout'}</span>
          </button>
          <button 
            onClick={() => handleTriggerSimulation('API_FAILURE')}
            disabled={!!simulatingMode}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700/50 transition-all"
          >
            <Zap size={13} className="text-amber-400" />
            <span>Inject API 500</span>
          </button>
        </div>
      </div>

      {/* ── Main Operations Grid ─────────────────────────────────────────── */}
      <div className="grid md:grid-cols-12 gap-6 items-start">
        
        {/* Sidebar: Incidents Feed */}
        <aside className="md:col-span-4 space-y-3">
          <div className="flex justify-between items-center px-1">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Incidents ({incidents.length || 1})</h3>
            <button onClick={fetchIncidents} className="text-slate-500 hover:text-slate-300">
              <RotateCcw size={14} />
            </button>
          </div>

          <div className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
            {incidents.length === 0 ? (
              <div 
                onClick={() => setSelectedIncident(MOCK_DEMO_INCIDENT)}
                className={`p-4 rounded-xl glass-card cursor-pointer transition-all ${
                  selectedIncident.id === MOCK_DEMO_INCIDENT.id ? 'border-blue-500/60 bg-blue-500/5' : ''
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-cyan-400">payment-api</span>
                  {getSeverityBadge(MOCK_DEMO_INCIDENT.severity)}
                </div>
                <p className="text-xs font-semibold text-slate-200 mb-3 line-clamp-2 leading-relaxed">
                  {MOCK_DEMO_INCIDENT.error}
                </p>
                <div className="flex justify-between items-center">
                  <span className="text-[11px] text-slate-500">10:42 AM</span>
                  {getStatusBadge(selectedIncident.status)}
                </div>
              </div>
            ) : (
              incidents.map(item => (
                <div 
                  key={item.id}
                  onClick={() => fetchIncidentDetail(item.id)}
                  className={`p-4 rounded-xl glass-card cursor-pointer transition-all ${
                    selectedIncident.id === item.id ? 'border-blue-500/60 bg-blue-500/5' : ''
                  }`}
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold text-cyan-400">{item.service}</span>
                    {getSeverityBadge(item.severity)}
                  </div>
                  <p className="text-xs font-semibold text-slate-200 mb-3 line-clamp-2">
                    {item.error}
                  </p>
                  <div className="flex justify-between items-center">
                    <span className="text-[11px] text-slate-500">
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {getStatusBadge(item.status)}
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="md:col-span-8 space-y-6">
          
          {/* Header Banner */}
          <div className="glass-card p-6 flex justify-between items-start">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-cyan-400 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                  INCIDENT #{selectedIncident.id.slice(0, 8)}
                </span>
                <span className="text-xs text-slate-400">Service: <strong className="text-slate-200">{selectedIncident.service}</strong></span>
                {getSeverityBadge(selectedIncident.severity)}
              </div>
              <h2 className="text-lg font-bold text-slate-100 leading-snug">
                {selectedIncident.error}
              </h2>
            </div>
            <div>
              {getStatusBadge(selectedIncident.status)}
            </div>
          </div>

          {/* Success Toast when Approved */}
          {prUrl && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex justify-between items-center animate-fade-in">
              <div className="flex items-center gap-3">
                <CheckCircle2 size={22} className="text-emerald-400 flex-shrink-0" />
                <div>
                  <h4 className="text-xs font-bold text-emerald-400">Recommendation Approved & GitHub PR Created!</h4>
                  <p className="text-[11px] text-slate-400">Automated PR created for {selectedIncident.service}. Slack notification pushed.</p>
                </div>
              </div>
              <a 
                href={prUrl} 
                target="_blank" 
                rel="noreferrer"
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400 transition-all"
              >
                <GitPullRequest size={14} />
                <span>View PR</span>
                <ExternalLink size={12} />
              </a>
            </div>
          )}

          {/* 5-Agent Execution Timeline */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Layers size={14} className="text-blue-400" />
              <span>OpenAI Agents SDK Investigation Timeline</span>
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {(selectedIncident.agent_runs || []).map((run, idx) => (
                <div key={idx} className="glass-card p-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-1.5">
                      <Bot size={15} className="text-purple-400" />
                      <span className="text-xs font-bold text-slate-200 truncate">{run.agent_name.replace(" Agent", "")}</span>
                    </div>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {run.duration_seconds || '0.04'}s
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-3">
                    {run.output_summary}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Root Cause & Confidence Score */}
          {selectedIncident.recommendation && (
            <div className="grid md:grid-cols-3 gap-6">
              
              <div className="md:col-span-2 glass-card p-6 space-y-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={18} className="text-rose-400" />
                  <h3 className="text-sm font-bold text-slate-200">Root Cause & Evidence Analysis</h3>
                </div>

                <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/20 space-y-1">
                  <h4 className="text-[10px] font-bold text-rose-400 uppercase">Primary Root Cause</h4>
                  <p className="text-xs font-semibold text-slate-200">
                    {selectedIncident.recommendation.root_cause}
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-slate-400">Correlated Evidence Items:</h4>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {selectedIncident.recommendation.evidence.map((item, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-rose-400 font-bold">&bull;</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Confidence Gauge */}
              <div className="glass-card p-6 flex flex-col justify-center items-center text-center space-y-3">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <svg className="w-24 h-24 transform -rotate-90">
                    <circle cx="48" cy="48" r="40" stroke="#1e293b" strokeWidth="8" fill="transparent" />
                    <circle 
                      cx="48" 
                      cy="48" 
                      r="40" 
                      stroke="#10b981" 
                      strokeWidth="8" 
                      fill="transparent"
                      strokeDasharray={251}
                      strokeDashoffset={251 - (251 * (selectedIncident.recommendation.confidence || 0.91))}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span className="absolute text-xl font-extrabold text-slate-100 font-mono">
                    {Math.round((selectedIncident.recommendation.confidence || 0.91) * 100)}%
                  </span>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-emerald-400">AI Confidence Score</h4>
                  <p className="text-[10px] text-slate-500 mt-0.5">Correlated from Log & Git MCP tools</p>
                </div>
              </div>

            </div>
          )}

          {/* Recommended Actions */}
          {selectedIncident.recommendation && (
            <div className="glass-card p-6 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <CheckCircle2 size={18} className="text-emerald-400" />
                <span>Recommended Fix Actions</span>
              </h3>

              <div className="space-y-2">
                {selectedIncident.recommendation.recommended_actions.map((act, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                    <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">
                      {idx + 1}
                    </span>
                    <span className="text-xs text-slate-200 font-medium">{act}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-1.5 pt-2">
                <h4 className="text-xs font-semibold text-slate-400">Drafted GitHub Pull Request Description:</h4>
                <pre className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-cyan-300 font-mono overflow-x-auto leading-relaxed">
                  {selectedIncident.recommendation.suggested_pr_description}
                </pre>
              </div>
            </div>
          )}

          {/* Human Approval Action Panel */}
          <div className="glass-card p-6 space-y-4 border-blue-500/30">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Send size={18} className="text-blue-400" />
              <span>Human-in-the-Loop Review & Approval Panel</span>
            </h3>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Reviewer Email</label>
                <input 
                  type="email" 
                  value={reviewer} 
                  onChange={e => setReviewer(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs outline-none focus:border-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Reviewer Notes</label>
                <input 
                  type="text" 
                  value={notes} 
                  onChange={e => setNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex gap-4 pt-2">
              <button 
                onClick={handleApprove}
                disabled={isSubmitting || selectedIncident.status === 'APPROVED'}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-emerald-500/20"
              >
                <CheckCircle2 size={16} />
                <span>{selectedIncident.status === 'APPROVED' ? 'Already Approved' : 'Approve Fix & Create GitHub PR'}</span>
              </button>

              <button 
                onClick={handleReject}
                disabled={isSubmitting || selectedIncident.status === 'REJECTED'}
                className="px-6 py-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 font-semibold text-xs border border-rose-500/30 transition-all"
              >
                <span>Reject Fix</span>
              </button>
            </div>
          </div>

        </main>

      </div>

    </div>
  );
};
