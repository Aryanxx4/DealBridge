import type { ComponentType } from "react";
import type { Assessment } from "@/types/api";

/** Page-level actions on the results tab (report download, sharing) registered as they are built. */
export const ResultsActions: ComponentType<{ assessment: Assessment; versionNo: number }>[] = [];
