export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type IncidentStatus = 
  | 'RECEIVED'
  | 'INVESTIGATING'
  | 'ANALYZED'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'RESOLVED';

export interface AgentFinding {
  agent_name: string;
  finding_type: string;
  content: string;
  evidence: any[];
  confidence: number;
}

export interface AgentRunResponse {
  agent_name: string;
  status: string;
  duration_seconds?: number;
  tokens_used?: number;
  output_summary: string;
}

export interface Recommendation {
  root_cause: string;
  evidence: string[];
  risk_level: Severity;
  recommended_actions: string[];
  confidence: number;
  suggested_pr_description: string;
  requires_immediate_action: boolean;
}

export interface IncidentResponse {
  id: string;
  error: string;
  service: string;
  severity: Severity;
  status: IncidentStatus;
  timestamp: string;
  created_at: string;
  findings: AgentFinding[];
  agent_runs: AgentRunResponse[];
  recommendation?: Recommendation;
  metadata: Record<string, any>;
}

export interface IncidentListItem {
  id: string;
  error: string;
  service: string;
  severity: Severity;
  status: IncidentStatus;
  timestamp: string;
  created_at: string;
}
