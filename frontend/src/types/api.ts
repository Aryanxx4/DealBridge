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
