import { api } from "@/services/api";
import type { DemoUser, HealthResponse } from "@/types/api";

export const identityApi = {
  users: () => api.get<DemoUser[]>("/identity/users"),
  health: () => api.get<HealthResponse>("/health"),
};
