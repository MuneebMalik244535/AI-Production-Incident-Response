import React from 'react';
import { 
  BookOpen, 
  Code, 
  FileText, 
  Globe, 
  Layers, 
  Terminal
} from 'lucide-react';

export const DocsPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-16">
      
      {/* Page Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-semibold text-purple-400">
          <BookOpen size={14} />
          <span>Documentation & Integration Guide</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-extrabold text-slate-100 tracking-tight">
          API Reference & Production Integration Guide
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Learn how to integrate your web applications via REST APIs, Sentry Webhooks, Express/FastAPI middleware, or Slack alerts.
        </p>
      </div>

      {/* ── REST API REFERENCE ──────────────────────────────────────────── */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Terminal size={24} className="text-blue-400" />
          <h2 className="text-2xl font-bold text-slate-100">REST API Reference</h2>
        </div>

        <div className="grid gap-4">
          
          {/* POST /api/incidents */}
          <div className="glass-card p-6 space-y-3">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 text-xs font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">POST</span>
              <span className="text-sm font-mono font-bold text-slate-100">/api/incidents</span>
              <span className="text-xs text-slate-400 ml-auto">Create Incident & Start Pipeline</span>
            </div>
            <p className="text-xs text-slate-300">
              Triggers the 5-agent investigation pipeline in the background. Returns incident ID immediately.
            </p>
            <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-cyan-300 font-mono overflow-x-auto">
{`curl -X POST http://localhost:8000/api/incidents \\
  -H "Content-Type: application/json" \\
  -d '{
    "error": "sqlalchemy.exc.TimeoutError: QueuePool limit reached",
    "service": "payment-api",
    "severity": "CRITICAL",
    "metadata": { "region": "us-east-1" }
  }'`}
            </pre>
          </div>

          {/* POST /api/incidents/{id}/approve */}
          <div className="glass-card p-6 space-y-3">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 text-xs font-bold rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">POST</span>
              <span className="text-sm font-mono font-bold text-slate-100">/api/incidents/{'{id}'}/approve</span>
              <span className="text-xs text-slate-400 ml-auto">Approve & Open GitHub PR</span>
            </div>
            <p className="text-xs text-slate-300">
              Human engineer approves the AI fix. Automatically creates a GitHub PR and sends a Slack notification.
            </p>
            <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-cyan-300 font-mono overflow-x-auto">
{`curl -X POST http://localhost:8000/api/incidents/inc-1234/approve \\
  -H "Content-Type: application/json" \\
  -d '{
    "decision": "APPROVE",
    "reviewer": "muneeb.malik@company.com",
    "notes": "Verified connection pool fix."
  }'`}
            </pre>
          </div>

        </div>
      </div>

      {/* ── MCP TOOL REGISTRY ───────────────────────────────────────────── */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Layers size={24} className="text-purple-400" />
          <h2 className="text-2xl font-bold text-slate-100">Model Context Protocol (MCP) Tool Servers</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="glass-card p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <FileText size={18} className="text-blue-400" />
              Log MCP Server (`log_server.py`)
            </h3>
            <p className="text-xs text-slate-400">Exposes FastMCP tools for log inspection and anomaly calculation.</p>
            <ul className="space-y-2 text-xs text-slate-300 font-mono">
              <li className="p-2 rounded bg-slate-900 border border-slate-800">search_logs(service, severity, time_range)</li>
              <li className="p-2 rounded bg-slate-900 border border-slate-800">get_log_entry(log_id)</li>
              <li className="p-2 rounded bg-slate-900 border border-slate-800">get_error_summary(service, time_range)</li>
            </ul>
          </div>

          <div className="glass-card p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Code size={18} className="text-cyan-400" />
              GitHub MCP Server (`github_server.py`)
            </h3>
            <p className="text-xs text-slate-400">Exposes FastMCP tools for commit and file diff analysis.</p>
            <ul className="space-y-2 text-xs text-slate-300 font-mono">
              <li className="p-2 rounded bg-slate-900 border border-slate-800">search_commits(repo, query, since_hours)</li>
              <li className="p-2 rounded bg-slate-900 border border-slate-800">get_commit(repo, sha)</li>
              <li className="p-2 rounded bg-slate-900 border border-slate-800">get_pull_request(repo, pr_number)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* ── TARGET WEBSITE INTEGRATION GUIDE ────────────────────────────── */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Globe size={24} className="text-emerald-400" />
          <h2 className="text-2xl font-bold text-slate-100">Connecting Any Target Website</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="glass-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-slate-100">FastAPI / Python Middleware</h3>
            <p className="text-xs text-slate-400">Add to your target python service exception handler:</p>
            <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-emerald-400 font-mono overflow-x-auto">
{`@app.exception_handler(Exception)
async def incident_handler(request, exc):
    async with httpx.AsyncClient() as client:
        await client.post("http://platform:8000/api/incidents", json={
            "error": str(exc),
            "service": "target-website",
            "severity": "CRITICAL"
        })`}
            </pre>
          </div>

          <div className="glass-card p-6 space-y-3">
            <h3 className="text-sm font-bold text-slate-100">Slack Webhook Setup</h3>
            <p className="text-xs text-slate-400">Add your Slack incoming webhook URL in backend `.env`:</p>
            <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-cyan-300 font-mono overflow-x-auto">
{`SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXX
GITHUB_TOKEN=ghp_your_personal_access_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/incidents`}
            </pre>
          </div>
        </div>
      </div>

    </div>
  );
};
