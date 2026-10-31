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

export type AnswerType =
  | "OFFICIAL_VERIFIED"
  | "EXPERT_VERIFIED"
  | "MIXED_VERIFIED"
  | "GENERAL_EXPLANATION"
  | "PARTIAL"
  | "UNVERIFIED"
  | "REDIRECT"
  | "OUT_OF_SCOPE"
  | "SMALL_TALK";

export interface Citation {
  n: number;
  collection: "OFFICIAL" | "RESOLVED";
  label: "Official documentation" | "Expert-verified answer";
  knowledge_id: string;
  chunk_id: string;
  title: string;
  heading_path: string;
  source_url: string | null;
  source_document: string | null;
  excerpt: string;
  version: number | null;
  last_verified_at: string | null;
  approved_at: string | null;
  relevance_score?: number; // admins only
}

export interface TicketRef {
  id: string;
  display_id: string;
  status: TicketStatus;
  linked: boolean;
}

export type TicketStatus = "OPEN" | "IN_REVIEW" | "ANSWER_PROPOSED" | "APPROVED" | "REJECTED" | "PUBLISHED" | "CLOSED";

export interface ChatMessage {
  id: string;
  role: "USER" | "ASSISTANT";
  content: string;
  answer_type: AnswerType | null;
  citations: Citation[];
  general_explanation_markdown: string | null;
  unverified_aspects: string[];
  conflict_note: string | null;
  action: { type: "OPEN_ASSESSMENT"; assessment_id: string | null } | null;
  ticket: TicketRef | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  assessment_id: string | null;
  requirement_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
  privacy_notice: string;
}

export interface TicketSummary {
  id: string;
  display_id: string;
  normalised_question: string;
  category: string;
  status: TicketStatus;
  priority: "LOW" | "MEDIUM" | "HIGH";
  reason: string;
  occurrence_count: number;
  created_at: string;
  updated_at: string;
  assigned_to: string | null;
}

export interface TraceHit {
  collection: "OFFICIAL" | "RESOLVED";
  knowledge_id: string;
  chunk_id: string;
  title: string;
  heading_path: string;
  score: number;
  excerpt: string;
}

export interface TicketDetail extends TicketSummary {
  original_question: string;
  context_excerpt: { role: string; content: string }[];
  retrieval_trace: {
    classification?: Record<string, unknown>;
    thresholds?: Record<string, number>;
    hits?: TraceHit[];
    decision?: string;
    duplicate_check?: Record<string, unknown>;
    faithfulness?: Record<string, unknown>;
  } | null;
  related_knowledge_ids: string[];
  linked_to_assessment: boolean;
  occurrences: { user: string | null; question_text: string; created_at: string }[];
  created_by: string | null;
  proposed_answer: string | null;
  proposed_by: string | null;
  proposed_by_id: string | null;
  proposed_at: string | null;
  supporting_sources: { title: string; url: string | null; note: string | null }[];
  internal_notes: string | null;
  reviewed_by: string | null;
  reviewer_note: string | null;
  reviewed_at: string | null;
  resolved_at: string | null;
  publish_error: string | null;
  published_knowledge_id: string | null;
  published_version: number | null;
  close_reason: string | null;
  allowed_actions: string[];
  allow_self_approval: boolean;
}

export interface Dashboard {
  tickets: { open: number; in_review: number; awaiting_approval: number; approved_unpublished: number; published: number; rejected: number; closed: number };
  published_knowledge_records: number;
  official_files_indexed: number;
  official_chunks: number | null;
  resolved_points: number | null;
}

export interface AuditRow {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  actor: string | null;
  actor_role: string | null;
  created_at: string;
}

export interface ResolvedRecord {
  id: string;
  knowledge_group_id: string;
  version: number;
  question_normalised: string;
  answer: string;
  category: string;
  validity: "ACTIVE" | "SUPERSEDED" | "REVOKED";
  status_reason: string | null;
  index_status: "PENDING" | "INDEXED" | "FAILED";
  indexed_at: string | null;
  author: string;
  approver: string;
  approved_at: string;
  ticket_display_id: string | null;
  supporting_references: { title: string; url: string | null; note: string | null }[];
}

export interface MyTicket {
  id: string;
  display_id: string;
  question: string;
  status: TicketStatus;
  created_at: string;
  occurrence_count: number;
  answer: { text: string; label: string; approved_at: string; version: number } | null;
}
