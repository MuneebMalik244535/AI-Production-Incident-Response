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

export interface PostMortemActionItem {
  action: string
  owner: string
  priority: string
  ticket_type: string
}

export interface PostMortemReport {
  incident_id: string
  service: string
  severity: string
  status: string
  generated_at: string
  summary: string
  impact: string
  root_cause: string
  evidence: string[]
  timeline: { time: string; event: string }[]
  investigation_duration_seconds: number
  recommended_actions: string[]
  action_items: PostMortemActionItem[]
  markdown_report: string
}

export interface HistoricalIncident {
  id: string
  service: string
  error_pattern: string
  root_cause: string
  verified_fix: string
  tags: string[]
  similarity_score: number
}

export interface StreamingEvent {
  incident_id: string
  event_type:
    | 'PIPELINE_STARTED'
    | 'AGENT_STARTED'
    | 'AGENT_FINDING'
    | 'ROOT_CAUSE_DEDUCED'
    | 'RECOMMENDATION_READY'
    | 'PIPELINE_COMPLETED'
    | string
  timestamp: string
  data: Record<string, any>
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

export async function fetchPostMortem(id: string): Promise<PostMortemReport> {
  const res = await fetch(`${API_BASE}/api/incidents/${id}/postmortem`)
  if (!res.ok) throw new Error(`Failed to fetch post-mortem for ${id}`)
  return res.json()
}

export async function searchIncidentMemory(
  service: string = '',
  query: string = '',
): Promise<HistoricalIncident[]> {
  const params = new URLSearchParams()
  if (service) params.set('service', service)
  if (query) params.set('query', query)
  const res = await fetch(`${API_BASE}/api/incidents/memory/search?${params.toString()}`)
  if (!res.ok) throw new Error('Failed to search incident memory')
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
  action: string = 'create_pr',
): Promise<IncidentResponse> {
  const res = await fetch(`${API_BASE}/api/incidents/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      decision: 'APPROVE',
      reviewer,
      notes,
      action,
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

export function createIncidentEventSource(
  incidentId: string,
  onEvent: (event: StreamingEvent) => void,
  onError?: (err: any) => void,
): () => void {
  const url = `${API_BASE}/api/incidents/${incidentId}/events`
  const es = new EventSource(url)

  es.onmessage = (msg) => {
    try {
      const parsed: StreamingEvent = JSON.parse(msg.data)
      onEvent(parsed)
    } catch (e) {
      // Ignored non-json heartbeat lines
    }
  }

  es.onerror = (err) => {
    if (onError) onError(err)
  }

  return () => {
    es.close()
  }
}
