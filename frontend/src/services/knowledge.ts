import { api } from "@/services/api";
import type { KnowledgeStatus } from "@/types/api";

export const knowledgeApi = {
  status: () => api.get<KnowledgeStatus>("/admin/knowledge/status"),
  reindex: () => api.post<{ job_id: string }>("/admin/knowledge/reindex"),
};
