import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { KnowledgePage } from "@/pages/admin/KnowledgePage";
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
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
