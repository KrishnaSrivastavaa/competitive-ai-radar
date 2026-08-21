export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

export interface Competitor {
  id: number;
  name: string;
  website_url: string;
  description: string | null;
  active: boolean;
}

export interface Source {
  id: number;
  competitor_id: number;
  name: string;
  url: string;
  source_type: string;
  active: boolean;
  extraction_description: string | null;
  collector_id: string | null;
}

export interface CollectionRun {
  id: number;
  source_id: number;
  status: "running" | "succeeded" | "failed" | string;
  started_at: string;
  finished_at: string | null;
  raw_result: JsonValue | null;
  record_count: number;
  error_message: string | null;
  health_status: "healthy" | "degraded" | "failed" | "unknown" | string;
  bright_data_collection_id: string | null;
}

export interface Snapshot {
  id: number;
  source_id: number;
  collection_run_id: number;
  captured_at: string;
  content_hash: string;
  normalized_data: JsonValue;
  evidence_url: string | null;
}

export interface Change {
  id: number;
  source_id: number;
  previous_snapshot_id: number | null;
  current_snapshot_id: number;
  change_type: "initial" | "unchanged" | "added" | "removed" | "modified" | string;
  summary: string;
  diff_data: JsonValue;
  significance: "none" | "low" | "medium" | "high" | string;
}

export interface InsightEvidence { source_url: string; reason: string; }

export interface Insight {
  id: number;
  competitor_id: number;
  change_id: number | null;
  title: string;
  analysis: string;
  competitive_impact: string;
  recommendation: string;
  confidence: number;
  evidence: InsightEvidence[];
  created_at: string;
}

export interface AgentEvidence { source_url: string; source_name: string; reason: string; }
export interface AgentAnswer { answer: string; evidence: AgentEvidence[]; }

export interface CompetitorWorkspaceData {
  competitor: Competitor;
  sources: Source[];
  runsBySource: Record<number, CollectionRun[]>;
  snapshotsBySource: Record<number, Snapshot[]>;
  changesBySource: Record<number, Change[]>;
  insights: Insight[];
}
