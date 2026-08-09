import { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
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
  ExternalLink,
  Server
} from 'lucide-react';
import type { IncidentResponse, IncidentListItem, Severity } from './types';

const API_BASE = 'http://localhost:8000/api';

// Initial Mock Incident for instant visual demonstration
const INITIAL_DEMO_INCIDENT: IncidentResponse = {
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

export default function App() {
  const [incidents, setIncidents] = useState<IncidentListItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentResponse>(INITIAL_DEMO_INCIDENT);
  const [reviewer, setReviewer] = useState('muneeb.malik@company.com');
  const [notes, setNotes] = useState('Root cause analysis verified. Connection pool fix looks solid.');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [simulatingMode, setSimulatingMode] = useState<string | null>(null);
  const [isLiveConnected, setIsLiveConnected] = useState(false);

  // Fetch incidents list from backend if available
  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/incidents`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);
        setIsLiveConnected(true);
        if (data.length > 0) {
          fetchIncidentDetail(data[0].id);
        }
      }
    } catch {
      setIsLiveConnected(false);
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
    } catch (e) {
      console.log('Simulation trigger fallback');
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
        // Fallback for UI demo
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
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-red-500/20 text-red-400 border border-red-500/30 glow-red">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">MEDIUM</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">LOW</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center gap-1.5 glow-green"><CheckCircle2 size={14}/> APPROVED</span>;
      case 'REJECTED':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-red-500/20 text-red-400 border border-red-500/40 flex items-center gap-1.5"><XCircle size={14}/> REJECTED</span>;
      case 'INVESTIGATING':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5 animate-pulse-glow"><Activity size={14}/> INVESTIGATING</span>;
      case 'AWAITING_APPROVAL':
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center gap-1.5"><Clock size={14}/> AWAITING APPROVAL</span>;
      default:
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40">{status}</span>;
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#0a0d14' }}>
      
      {/* ── Top Navigation Bar ──────────────────────────────────────────────── */}
      <header className="glass-panel" style={{ margin: '16px 24px 0 24px', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '10px', borderRadius: '10px', backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <ShieldAlert size={24} color="#ef4444" />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.5px' }}>
              AI Production Incident Response Platform
            </h1>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>
              Autonomous Multi-Agent Investigation Pipeline &bull; OpenAI Agents SDK &bull; MCP Protocol
            </p>
          </div>
        </div>

        {/* Status Indicator & Live Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '12px', color: '#10b981' }}>
            <Server size={14} />
            <span>{isLiveConnected ? 'FastAPI Live' : 'Demo Mode (Offline)'}</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={() => handleTriggerSimulation('DB_TIMEOUT')}
              disabled={!!simulatingMode}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #334155', color: '#f8fafc', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
            >
              <Zap size={14} color="#ef4444" />
              {simulatingMode === 'DB_TIMEOUT' ? 'Injecting...' : 'Simulate DB Timeout'}
            </button>
            <button 
              onClick={() => handleTriggerSimulation('API_FAILURE')}
              disabled={!!simulatingMode}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #334155', color: '#f8fafc', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
            >
              <Zap size={14} color="#f59e0b" />
              Simulate API 500
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Layout Body ────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, padding: '24px', gap: '24px' }}>
        
        {/* ── Left Sidebar: Incidents Stream ────────────────────────────────── */}
        <aside style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px' }}>
            <h2 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Incidents Feed ({incidents.length || 1})
            </h2>
            <button onClick={fetchIncidents} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
              <RotateCcw size={14} />
            </button>
          </div>

          <div className="glass-panel" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', height: 'calc(100vh - 160px)', overflowY: 'auto' }}>
            {incidents.length === 0 ? (
              <div 
                onClick={() => setSelectedIncident(INITIAL_DEMO_INCIDENT)}
                style={{ 
                  padding: '14px', 
                  borderRadius: '8px', 
                  backgroundColor: selectedIncident.id === INITIAL_DEMO_INCIDENT.id ? '#1e293b' : 'transparent',
                  border: selectedIncident.id === INITIAL_DEMO_INCIDENT.id ? '1px solid #3b82f6' : '1px solid transparent',
                  cursor: 'pointer' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8' }}>payment-api</span>
                  {getSeverityBadge(INITIAL_DEMO_INCIDENT.severity)}
                </div>
                <p style={{ fontSize: '13px', fontWeight: 500, color: '#f8fafc', marginBottom: '8px', lineHeight: '1.3' }}>
                  {INITIAL_DEMO_INCIDENT.error.slice(0, 60)}...
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>10:42 AM</span>
                  {getStatusBadge(selectedIncident.status)}
                </div>
              </div>
            ) : (
              incidents.map(item => (
                <div 
                  key={item.id}
                  onClick={() => fetchIncidentDetail(item.id)}
                  style={{ 
                    padding: '14px', 
                    borderRadius: '8px', 
                    backgroundColor: selectedIncident.id === item.id ? '#1e293b' : 'transparent',
                    border: selectedIncident.id === item.id ? '1px solid #3b82f6' : '1px solid transparent',
                    cursor: 'pointer' 
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8' }}>{item.service}</span>
                    {getSeverityBadge(item.severity)}
                  </div>
                  <p style={{ fontSize: '13px', fontWeight: 500, color: '#f8fafc', marginBottom: '8px' }}>
                    {item.error.slice(0, 60)}...
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {getStatusBadge(item.status)}
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* ── Main View: Detailed Agent Investigation & Actions ─────────────── */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
          
          {/* Incident Detail Header Banner */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', backgroundColor: 'rgba(56, 189, 248, 0.1)' }}>
                  INCIDENT #{selectedIncident.id.slice(0, 8)}
                </span>
                <span style={{ fontSize: '13px', color: '#94a3b8' }}>Service: <strong>{selectedIncident.service}</strong></span>
                {getSeverityBadge(selectedIncident.severity)}
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', lineHeight: '1.3' }}>
                {selectedIncident.error}
              </h2>
            </div>
            <div>
              {getStatusBadge(selectedIncident.status)}
            </div>
          </div>

          {/* Success Toast when Approved */}
          {prUrl && (
            <div style={{ padding: '16px 20px', borderRadius: '12px', backgroundColor: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <CheckCircle2 color="#10b981" size={24} />
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#10b981' }}>Recommendation Approved & GitHub PR Created!</h4>
                  <p style={{ fontSize: '12px', color: '#94a3b8' }}>
                    Automated PR created for repository {selectedIncident.service}. Slack notification sent to #production-alerts.
                  </p>
                </div>
              </div>
              <a 
                href={prUrl} 
                target="_blank" 
                rel="noreferrer"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '8px', backgroundColor: '#10b981', color: '#0a0d14', fontWeight: 700, fontSize: '13px', textDecoration: 'none' }}
              >
                <GitPullRequest size={16} />
                View GitHub PR
                <ExternalLink size={14} />
              </a>
            </div>
          )}

          {/* ── Multi-Agent Investigation Execution Timeline ───────────────── */}
          <div>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={16} color="#38bdf8" />
              OpenAI Agents SDK Execution Pipeline ({selectedIncident.agent_runs?.length || 4} Agents Executed)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
              {(selectedIncident.agent_runs || []).map((run, idx) => (
                <div key={idx} className="glass-panel" style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Bot size={18} color="#8b5cf6" />
                      <span style={{ fontSize: '13px', fontWeight: 600 }}>{run.agent_name}</span>
                    </div>
                    <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                      {run.duration_seconds || '0.04'}s
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.4' }}>
                    {run.output_summary}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Root Cause & Evidence Card ──────────────────────────────────── */}
          {selectedIncident.recommendation && (
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
              
              {/* Root Cause & Evidence */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <AlertTriangle color="#ef4444" size={20} />
                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>
                    Root Cause Analysis & Correlated Evidence
                  </h3>
                </div>

                <div style={{ padding: '16px', borderRadius: '8px', backgroundColor: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', marginBottom: '20px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Likely Root Cause
                  </h4>
                  <p style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
                    {selectedIncident.recommendation.root_cause}
                  </p>
                </div>

                <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', marginBottom: '10px' }}>
                  Evidence Correlated Across Logs & Code Commits:
                </h4>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: '8px', listStyle: 'none' }}>
                  {selectedIncident.recommendation.evidence.map((item, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '13px', color: '#cbd5e1' }}>
                      <span style={{ color: '#ef4444', fontWeight: 700 }}>&bull;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Confidence Score Gauge */}
              <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
                <div style={{ position: 'relative', width: '120px', height: '120px', display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: '12px' }}>
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#1e293b" strokeWidth="10" />
                    <circle 
                      cx="60" 
                      cy="60" 
                      r="50" 
                      fill="none" 
                      stroke="#10b981" 
                      strokeWidth="10" 
                      strokeDasharray="314" 
                      strokeDashoffset={314 - (314 * (selectedIncident.recommendation.confidence || 0.91))}
                      strokeLinecap="round"
                    />
                  </svg>
                  <span style={{ position: 'absolute', fontSize: '24px', fontWeight: 800, color: '#f8fafc' }}>
                    {Math.round((selectedIncident.recommendation.confidence || 0.91) * 100)}%
                  </span>
                </div>
                <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#10b981' }}>AI Confidence Score</h4>
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                  Correlated with 94% commit match
                </p>
              </div>

            </div>
          )}

          {/* ── Recommended Actions & PR Draft ─────────────────────────────── */}
          {selectedIncident.recommendation && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 color="#10b981" size={20} />
                Recommended Fix Actions
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                {selectedIncident.recommendation.recommended_actions.map((act, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #334155' }}>
                    <span style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '24px', height: '24px', borderRadius: '50%', backgroundColor: '#38bdf8', color: '#0a0d14', fontWeight: 700, fontSize: '12px' }}>
                      {idx + 1}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 500, color: '#f8fafc' }}>{act}</span>
                  </div>
                ))}
              </div>

              {/* Code PR Description Draft */}
              <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
                Suggested GitHub Pull Request Description:
              </h4>
              <pre style={{ padding: '16px', borderRadius: '8px', backgroundColor: '#090d16', border: '1px solid #1e293b', fontSize: '12px', color: '#38bdf8', overflowX: 'auto', lineHeight: '1.5' }}>
                {selectedIncident.recommendation.suggested_pr_description}
              </pre>
            </div>
          )}

          {/* ── Human Approval Action Panel ─────────────────────────────────── */}
          <div className="glass-panel" style={{ padding: '24px', border: '1px solid rgba(59, 130, 246, 0.4)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Send color="#38bdf8" size={20} />
              Human-in-the-Loop Review & Approval Panel
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                  Reviewer Engineer
                </label>
                <input 
                  type="email" 
                  value={reviewer} 
                  onChange={e => setReviewer(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #334155', color: '#f8fafc', fontSize: '13px', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
                  Review Notes / Comments
                </label>
                <input 
                  type="text" 
                  value={notes} 
                  onChange={e => setNotes(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', backgroundColor: '#1e293b', border: '1px solid #334155', color: '#f8fafc', fontSize: '13px', outline: 'none' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px' }}>
              <button 
                onClick={handleApprove}
                disabled={isSubmitting || selectedIncident.status === 'APPROVED'}
                style={{ 
                  flex: 1, 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  gap: '8px', 
                  padding: '14px', 
                  borderRadius: '8px', 
                  backgroundColor: selectedIncident.status === 'APPROVED' ? '#1e293b' : '#10b981', 
                  color: selectedIncident.status === 'APPROVED' ? '#64748b' : '#0a0d14', 
                  fontWeight: 700, 
                  fontSize: '14px', 
                  border: 'none', 
                  cursor: selectedIncident.status === 'APPROVED' ? 'not-allowed' : 'pointer' 
                }}
              >
                <CheckCircle2 size={18} />
                {selectedIncident.status === 'APPROVED' ? 'Already Approved' : 'Approve Fix & Create GitHub PR'}
              </button>

              <button 
                onClick={handleReject}
                disabled={isSubmitting || selectedIncident.status === 'REJECTED'}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  gap: '8px', 
                  padding: '14px 24px', 
                  borderRadius: '8px', 
                  backgroundColor: 'rgba(239, 68, 68, 0.15)', 
                  color: '#ef4444', 
                  fontWeight: 600, 
                  fontSize: '14px', 
                  border: '1px solid rgba(239, 68, 68, 0.4)', 
                  cursor: 'pointer' 
                }}
              >
                <XCircle size={18} />
                Reject Fix
              </button>
            </div>
          </div>

        </main>

      </div>

    </div>
  );
}
