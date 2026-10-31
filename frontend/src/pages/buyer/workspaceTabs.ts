import type { ComponentType } from "react";
import type { Assessment } from "@/types/api";

/** Further workspace tabs (results, versions, sharing) are registered here as they are built. */
export const WORKSPACE_TABS: { value: string; label: string; Component: ComponentType<{ assessment: Assessment }> }[] = [];
