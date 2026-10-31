import { api } from "@/services/api";
import type { Job } from "@/types/api";

export const jobsApi = { get: (id: string) => api.get<Job>(`/jobs/${id}`) };
