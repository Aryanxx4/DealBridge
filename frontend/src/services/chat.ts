import { api } from "@/services/api";
import type { ChatMessage, ChatSession, ChatSessionDetail } from "@/types/api";

export const chatApi = {
  suggested: () => api.get<{ questions: string[] }>("/chat/suggested-questions"),
  sessions: () => api.get<ChatSession[]>("/chat/sessions"),
  session: (id: string) => api.get<ChatSessionDetail>(`/chat/sessions/${id}`),
  create: (body: { title?: string; assessment_id?: string | null; requirement_id?: string | null } = {}) => api.post<ChatSession>("/chat/sessions", body),
  send: (id: string, content: string) => api.post<{ user_message: ChatMessage; assistant_message: ChatMessage }>(`/chat/sessions/${id}/messages`, { content }),
  raiseTicket: (messageId: string) => api.post<ChatMessage>(`/chat/messages/${messageId}/raise-ticket`),
};
