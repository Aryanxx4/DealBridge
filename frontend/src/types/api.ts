// Mirrors backend/app/core/enums.py and the Pydantic response schemas.

export type UserRole = "BUYER" | "SELLER" | "ADMIN";
export type OrgKind = "BUYER_ORG" | "SELLER_ORG" | "INTERNAL";

export interface Organization {
  id: string;
  name: string;
  kind: OrgKind;
}

export interface DemoUser {
  id: string;
  display_name: string;
  email: string;
  role: UserRole;
  organization: Organization;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  dependencies: {
    postgres: { ok: boolean };
    qdrant: { ok: boolean };
    embedding_model: { ok: boolean; model: string; error: string | null };
    llm: { configured: boolean; provider: string };
  };
  reindex_required: boolean;
  reindex_problems: string[];
  embedding_loading: boolean;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> };
}

export type JobStatus = "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface Job {
  id: string;
  type: "EXTRACT_PDF" | "ANALYZE" | "REINDEX";
  status: JobStatus;
  assessment_id: string | null;
  progress_done: number;
  progress_total: number;
  progress_message: string | null;
  result: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface IngestionRunSummary {
  id: string;
  started_at: string;
  finished_at: string | null;
  triggered_by: string;
  mode: string;
  spec_conformance: string;
  embedding_model: string;
  files_scanned: number;
  added: number;
  updated: number;
  unchanged: number;
  removed: number;
  skipped: number;
  chunks_upserted: number;
  chunks_deleted: number;
  errors: { path: string; error: string }[];
  status: string;
}

export interface OkfFileRow {
  path: string;
  knowledge_id: string | null;
  title: string | null;
  category: string | null;
  source_url: string | null;
  content_hash: string;
  status: "INDEXED" | "SKIPPED_NOT_APPROVED" | "REMOVED" | "ERROR";
  chunk_count: number;
  last_verified_at: string | null;
  version: number | null;
  error: string | null;
  last_ingested_at: string | null;
}

export interface KnowledgeStatus {
  spec: { format: string; version: string; source: string };
  qdrant_ok: boolean;
  points: { official: number | null; resolved: number | null };
  epoch: number;
  reindex_required: boolean;
  reindex_problems: string[];
  last_run: IngestionRunSummary | null;
  running_job_id: string | null;
  files: OkfFileRow[];
}
