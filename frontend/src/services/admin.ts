import { api } from "@/services/api";
import type { AuditRow, Dashboard, MyTicket, ResolvedRecord, TicketDetail, TicketSummary } from "@/types/api";

export interface AnswerBody {
  normalised_question: string;
  category: string;
  answer: string;
  supporting_sources: { title: string; url?: string | null; note?: string | null }[];
  internal_notes?: string | null;
  privacy_confirmed: boolean;
}

export const adminApi = {
  dashboard: () => api.get<Dashboard>("/admin/dashboard"),
  audit: (limit = 15) => api.get<AuditRow[]>(`/admin/audit?limit=${limit}`),
  tickets: (status?: string) => api.get<TicketSummary[]>(`/admin/tickets${status ? `?status=${status}` : ""}`),
  ticket: (id: string) => api.get<TicketDetail>(`/admin/tickets/${id}`),
  action: (id: string, action: string, body?: Record<string, unknown>) => api.post<TicketDetail>(`/admin/tickets/${id}/${action}`, body),
  answer: (id: string, body: AnswerBody) => api.post<TicketDetail>(`/admin/tickets/${id}/answer`, body as unknown as Record<string, unknown>),
  resolved: () => api.get<ResolvedRecord[]>("/admin/knowledge"),
  supersede: (id: string, body: { answer: string; question_normalised?: string; privacy_confirmed: boolean }) => api.post<ResolvedRecord>(`/admin/knowledge/${id}/supersede`, body),
  revoke: (id: string, reason: string) => api.post<ResolvedRecord>(`/admin/knowledge/${id}/revoke`, { reason }),
};

export const myQuestionsApi = { list: () => api.get<MyTicket[]>("/chat/tickets") };
