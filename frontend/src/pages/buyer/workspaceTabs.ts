import type { ComponentType } from "react";
import type { Assessment } from "@/types/api";
import { ResultsTab } from "./results/ResultsTab";
import { VersionsTab } from "./results/VersionsTab";
import { ShareTab } from "./sharing/ShareTab";

/** Workspace tabs after "Requirements"; further tabs are registered here as they are built. */
export const WORKSPACE_TABS: { value: string; label: string; Component: ComponentType<{ assessment: Assessment }> }[] = [
  { value: "results", label: "Results", Component: ResultsTab },
  { value: "versions", label: "Versions", Component: VersionsTab },
  { value: "share", label: "Share and follow-ups", Component: ShareTab },
];
