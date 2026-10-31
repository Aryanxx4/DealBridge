import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { AdminDashboardPage } from "@/pages/admin/AdminDashboardPage";
import { KnowledgePage } from "@/pages/admin/KnowledgePage";
import { TicketDetailPage } from "@/pages/admin/TicketDetailPage";
import { MyQuestionsPage } from "@/pages/chatbot/MyQuestionsPage";
import { ChatPage } from "@/pages/chatbot/ChatPage";
import { LandingPage } from "@/pages/landing/LandingPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/admin/knowledge", element: <KnowledgePage /> },
      { path: "/chat", element: <ChatPage /> },
      { path: "/chat/questions", element: <MyQuestionsPage /> },
      { path: "/admin", element: <AdminDashboardPage /> },
      { path: "/admin/tickets/:id", element: <TicketDetailPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
