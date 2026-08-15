const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type IncidentStatus =
  | 'RECEIVED'
  | 'INVESTIGATING'
  | 'ANALYZED'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'RESOLVED'

export interface IncidentListItem {
  id: string
  service: string
  error: string
  severity: Severity
  status: IncidentStatus
  timestamp: string
  created_at: string
}

export interface AgentFinding {
  agent_name: string
  finding_type: string
  content: string
  evidence: Record<string, any>[]
  confidence: number
}

export interface AgentRunResponse {
  agent_name: string
  status: string
  duration_seconds?: number
  tokens_used?: number
  output_summary: string
}

export interface Recommendation {
  root_cause: string
  evidence: string[]
  risk_level: Severity
  recommended_actions: string[]
  confidence: number
  suggested_pr_description: string
  requires_immediate_action: boolean
}

export interface IncidentResponse {
  id: string
  error: string
  service: string
  severity: Severity
  status: IncidentStatus
  timestamp: string
  created_at: string
  findings: AgentFinding[]
  agent_runs: AgentRunResponse[]
  recommendation?: Recommendation
  metadata: Record<string, any>
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Health check failed')
  return res.json()
}

export async function fetchIncidents(): Promise<IncidentListItem[]> {
  const res = await fetch(`${API_BASE}/api/incidents`)
  if (!res.ok) throw new Error('Failed to fetch incidents')
  return res.json()
}

export async function fetchIncident(id: string): Promise<IncidentResponse> {
  const res = await fetch(`${API_BASE}/api/incidents/${id}`)
  if (!res.ok) throw new Error(`Failed to fetch incident ${id}`)
  return res.json()
}

export async function injectFailure(type: 'db' | 'api' | 'auth'): Promise<IncidentResponse> {
  const res = await fetch(`${API_BASE}/api/incidents/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type }),
  })
  if (!res.ok) throw new Error('Failed to inject failure')
  return res.json()
}

export async function approveIncident(
  id: string,
  reviewer: string,
  notes: string,
): Promise<IncidentResponse> {
  const res = await fetch(`${API_BASE}/api/incidents/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      decision: 'APPROVE',
      reviewer,
      notes,
      action: 'create_pr',
    }),
  })
  if (!res.ok) throw new Error(`Failed to approve incident ${id}`)
  return res.json()
}

export async function rejectIncident(
  id: string,
  reviewer: string,
  notes: string,
): Promise<IncidentResponse> {
  const res = await fetch(`${API_BASE}/api/incidents/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      decision: 'REJECT',
      reviewer,
      notes,
      action: 'reject',
    }),
  })
  if (!res.ok) throw new Error(`Failed to reject incident ${id}`)
  return res.json()
}
