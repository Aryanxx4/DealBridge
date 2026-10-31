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

export type AssessmentStatus = "DRAFT" | "ANALYZING" | "ANALYZED" | "STALE";
export type Priority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NOT_SPECIFIED";
export type RequirementCategory =
  | "FUNCTIONAL_CAPABILITY"
  | "DEPLOYMENT_INFRASTRUCTURE"
  | "DATA_SOVEREIGNTY_RESIDENCY"
  | "SECURITY_ACCESS_CONTROL"
  | "INTEGRATION_COMPATIBILITY"
  | "PERFORMANCE_SCALABILITY"
  | "AVAILABILITY_RELIABILITY"
  | "COMPLIANCE_GOVERNANCE"
  | "COST_OPERATIONS"
  | "OTHER";

export const CATEGORY_LABELS: Record<RequirementCategory, string> = {
  FUNCTIONAL_CAPABILITY: "Functional capability",
  DEPLOYMENT_INFRASTRUCTURE: "Deployment and infrastructure",
  DATA_SOVEREIGNTY_RESIDENCY: "Data sovereignty and residency",
  SECURITY_ACCESS_CONTROL: "Security and access control",
  INTEGRATION_COMPATIBILITY: "Integration and compatibility",
  PERFORMANCE_SCALABILITY: "Performance and scalability",
  AVAILABILITY_RELIABILITY: "Availability and reliability",
  COMPLIANCE_GOVERNANCE: "Compliance and governance",
  COST_OPERATIONS: "Cost and operations",
  OTHER: "Other",
};

export const PRIORITY_LABELS: Record<Priority, string> = { CRITICAL: "Critical", HIGH: "High", MEDIUM: "Medium", LOW: "Low", NOT_SPECIFIED: "Not specified" };

export interface Assessment {
  id: string;
  title: string;
  status: AssessmentStatus;
  context: { organisation_name?: string; industry?: string; use_case?: string };
  intake_form: Record<string, unknown> | null;
  requirement_set_revision: number;
  latest_version_no: number;
  requirement_count: number;
  confirmed_count: number;
  created_at: string;
  updated_at: string;
}

export interface UploadedDocument {
  id: string;
  original_filename: string;
  size_bytes: number;
  page_count: number;
  sha256: string;
  extraction_status: "OK" | "SCANNED" | "EMPTY" | "MALFORMED";
  extraction_message: string | null;
  created_at: string;
}

export interface Requirement {
  id: string;
  display_id: string;
  seq: number;
  original_text: string;
  normalized_text: string;
  category: RequirementCategory;
  priority: Priority;
  priority_basis: string | null;
  source_type: "PDF" | "CHAT" | "FORM" | "MANUAL";
  source_reference: { document_id?: string; filename?: string; page?: number | null; quote?: string; quote_verified?: boolean; field_key?: string; field_label?: string; message_id?: string };
  buyer_confirmed: boolean;
  needs_clarification: boolean;
  clarifying_question: string | null;
  clarification_waived: boolean;
  is_removed: boolean;
  removed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RequirementRevision {
  revision_no: number;
  change_type: string;
  changes: Record<string, { before: unknown; after: unknown } | string>;
  actor: string | null;
  origin: string;
  assessment_revision: number;
  created_at: string;
}

export interface ProposedOp {
  op: "ADD" | "UPDATE" | "REMOVE";
  target_display_id: string | null;
  normalized_text: string | null;
  category: RequirementCategory | null;
  priority: Priority | null;
  source_quote: string;
  target_snapshot?: { normalized_text: string };
}

export interface ChangeProposal {
  id: string;
  status: "PENDING" | "APPLIED" | "DISMISSED";
  ops: ProposedOp[];
  applied_op_indexes: number[];
  result: { changed: { op: string; display_id: string; text: string }[] } | null;
  message_id: string | null;
}

export interface IntakeMessage {
  id: string;
  role: "USER" | "ASSISTANT";
  content: string;
  structured?: { clarifying_questions?: string[]; assumptions_noted?: string[] } | null;
  created_at: string;
}

export type FitStatus = "SUPPORTED" | "PARTIALLY_SUPPORTED" | "NEEDS_VALIDATION" | "NOT_SUPPORTED" | "UNKNOWN";

export interface EvidenceItem {
  rank: number;
  role: "SUPPORTS" | "LIMITS" | "RELATED";
  collection: "OFFICIAL" | "RESOLVED";
  label: "Official documentation" | "Expert-verified answer";
  knowledge_id: string;
  chunk_id: string;
  title: string;
  heading_path: string | null;
  source_url: string | null;
  source_document: string | null;
  excerpt: string;
  version: number | null;
  last_verified_at: string | null;
  approved_at: string | null;
}

export interface SellerResponse {
  id: string;
  seller_name: string;
  seller_org: string;
  assertion: "NONE" | "CONFIRMS_SUPPORT" | "CONFIRMS_LIMITATION" | "NEEDS_INFO_FROM_BUYER";
  body: string;
  created_at: string;
  version_no: number;
}

export interface RequirementResult {
  requirement_id: string;
  display_id: string;
  text: string;
  original_text: string | null;
  category: RequirementCategory;
  priority: Priority;
  source_type: string | null;
  source_quote: string | null;
  source_page: number | null;
  status: FitStatus;
  explanation: { meaning?: string; established?: string; unverified?: string; next_step?: string };
  supported_part: string | null;
  unestablished_part: string | null;
  assumptions: string[];
  missing_information: string[];
  questions_for_seller: string[];
  has_conflict: boolean;
  conflict_description: string | null;
  is_blocker: boolean;
  guardrail_notes: string[];
  candidate_count: number | null;
  evidence: EvidenceItem[];
  open_ticket: { id: string; display_id: string; status: TicketStatus } | null;
  answer_available: boolean;
  seller_responses: SellerResponse[];
}

export interface VersionChange {
  requirement_id: string;
  display_id: string;
  change: "ADDED" | "REMOVED" | "TEXT_CHANGED" | "PRIORITY_CHANGED" | "STATUS_CHANGED" | "UNCHANGED";
  previous_text: string | null;
  new_text: string | null;
  previous_priority: Priority | null;
  new_priority: Priority | null;
  previous_status: FitStatus | null;
  new_status: FitStatus | null;
}

export interface AssessmentResults {
  assessment: { id: string; title: string; status: AssessmentStatus; context: Assessment["context"] };
  version: { version_no: number; analyzed_at: string; requirement_set_revision: number; knowledge_epoch: number; model: string | null };
  summary: {
    executive_summary: string;
    status_counts: Record<FitStatus, number>;
    blockers: string[];
    next_steps: string[];
    assumptions: string[];
    missing_information: string[];
    questions_for_seller: string[];
  };
  knowledge_updated: boolean;
  changes_since_previous: VersionChange[] | null;
  requirements: RequirementResult[];
}

export interface VersionRow {
  version_no: number;
  analyzed_at: string;
  requirement_set_revision: number;
  status_counts: Record<FitStatus, number>;
  requirement_count: number;
}

export interface SellerOrg {
  id: string;
  name: string;
}

export interface ShareRow {
  id: string;
  seller_org_id: string;
  seller_org: string;
  version_no: number;
  shared_at: string;
  revoked_at: string | null;
  active: boolean;
}

export type FollowUpStatus = "REQUESTED" | "IN_PROGRESS" | "RESPONDED" | "CLOSED";

export interface FollowUp {
  id: string;
  assessment_id: string;
  assessment_title: string | null;
  seller_org: string;
  seller_org_id: string;
  requested_by: string;
  buyer_org: string;
  subject: string;
  related_requirement_ids: string[];
  status: FollowUpStatus;
  seller_decision: "PENDING" | "ACCEPTED" | "REJECTED";
  decision_reason: string | null;
  assigned_owner: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  allowed_actions: string[];
  messages?: { id: string; author: string; author_org: string; author_role: string; body: string; created_at: string }[];
}

export interface SellerAssessmentRow {
  id: string;
  title: string;
  buyer_name: string | null;
  buyer_org: string | null;
  shared_version: number;
  shared_at: string;
  status_counts: Record<FitStatus, number>;
  open_follow_ups: number;
}

export interface SellerAssessmentView extends AssessmentResults {
  shared_versions: number[];
  assessment: AssessmentResults["assessment"] & { buyer_name: string | null; buyer_org: string | null };
}
