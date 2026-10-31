import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { storeUserId } from "./services/api";

// Development convenience only (stripped from production builds): ?demo_user=<id> selects a demo identity.
if (import.meta.env.DEV) {
  const url = new URL(window.location.href);
  const demo = url.searchParams.get("demo_user");
  if (demo) {
    storeUserId(demo);
    url.searchParams.delete("demo_user");
    window.history.replaceState(null, "", url.toString());
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
