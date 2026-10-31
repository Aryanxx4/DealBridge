import { api } from "@/services/api";
import type { Assessment, ChangeProposal, IntakeMessage, Requirement, RequirementRevision, UploadedDocument } from "@/types/api";

export const assessmentsApi = {
  list: () => api.get<Assessment[]>("/assessments"),
  get: (id: string) => api.get<Assessment>(`/assessments/${id}`),
  create: (body: { title: string; context: Record<string, string> }) => api.post<Assessment>("/assessments", body),
  patch: (id: string, body: Record<string, unknown>) => api.patch<Assessment>(`/assessments/${id}`, body),
  documents: (id: string) => api.get<UploadedDocument[]>(`/assessments/${id}/documents`),
  upload: (id: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post<UploadedDocument>(`/assessments/${id}/documents`, fd);
  },
  extract: (id: string, documentId: string) => api.post<{ job_id: string }>(`/assessments/${id}/requirements/extract`, { document_id: documentId }),
  submitForm: (id: string, form: Record<string, unknown>) => api.post<{ created: number; removed: number; changed_fields: string[] }>(`/assessments/${id}/form`, form),
  requirements: (id: string, includeRemoved = false) => api.get<Requirement[]>(`/assessments/${id}/requirements${includeRemoved ? "?include_removed=true" : ""}`),
  addRequirement: (id: string, body: { normalized_text: string; category: string; priority: string }) => api.post<Requirement>(`/assessments/${id}/requirements`, body),
  confirmAll: (id: string) => api.post<{ confirmed: string[] }>(`/assessments/${id}/requirements/confirm-all`),
  intake: (id: string) => api.get<{ messages: IntakeMessage[]; proposals: ChangeProposal[] }>(`/assessments/${id}/intake-chat`),
  sendIntake: (id: string, content: string) => api.post<{ user_message: IntakeMessage; assistant_message: IntakeMessage; proposal: ChangeProposal | null }>(`/assessments/${id}/intake-chat/messages`, { content }),
  applyProposal: (id: string, pid: string, indexes: number[]) => api.post<{ changed: { op: string; display_id: string }[] }>(`/assessments/${id}/change-proposals/${pid}/apply`, { selected_op_indexes: indexes }),
  dismissProposal: (id: string, pid: string) => api.post<ChangeProposal>(`/assessments/${id}/change-proposals/${pid}/dismiss`),
};

export const requirementsApi = {
  patch: (id: string, body: Partial<Pick<Requirement, "normalized_text" | "category" | "priority">>) => api.patch<Requirement>(`/requirements/${id}`, body),
  remove: (id: string) => api.del<Requirement>(`/requirements/${id}`),
  restore: (id: string) => api.post<Requirement>(`/requirements/${id}/restore`),
  confirm: (id: string) => api.post<Requirement>(`/requirements/${id}/confirm`),
  waive: (id: string) => api.post<Requirement>(`/requirements/${id}/waive-clarification`),
  history: (id: string) => api.get<RequirementRevision[]>(`/requirements/${id}/history`),
};
