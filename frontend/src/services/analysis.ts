import { api } from "@/services/api";
import type { AssessmentResults, VersionChange, VersionRow } from "@/types/api";

export const analysisApi = {
  run: (id: string) => api.post<{ job_id: string }>(`/assessments/${id}/analyze`),
  results: (id: string, version?: number) => api.get<AssessmentResults>(`/assessments/${id}/results${version ? `?version=${version}` : ""}`),
  versions: (id: string) => api.get<VersionRow[]>(`/assessments/${id}/versions`),
  compare: (id: string, a: number, b: number) => api.get<{ changes: VersionChange[] }>(`/assessments/${id}/versions/${a}/compare/${b}`),
  pending: (id: string) => api.get<{ changes: VersionChange[] }>(`/assessments/${id}/pending-changes`),
};
