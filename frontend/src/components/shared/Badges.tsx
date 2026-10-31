import { cn } from "@/lib/utils";
import { type AssessmentStatus, type Priority, PRIORITY_LABELS } from "@/types/api";

const PRIORITY_CLS: Record<Priority, string> = {
  CRITICAL: "bg-red-50 text-red-800 border-red-200",
  HIGH: "bg-orange-50 text-orange-800 border-orange-200",
  MEDIUM: "bg-blue-50 text-blue-800 border-blue-200",
  LOW: "bg-slate-50 text-slate-700 border-slate-200",
  NOT_SPECIFIED: "bg-white text-slate-500 border-slate-200",
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", PRIORITY_CLS[priority])}>{PRIORITY_LABELS[priority]}</span>;
}

const STATUS: Record<AssessmentStatus, { label: string; cls: string }> = {
  DRAFT: { label: "Draft", cls: "bg-slate-100 text-slate-700 border-slate-200" },
  ANALYZING: { label: "Analyzing", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  ANALYZED: { label: "Analyzed", cls: "bg-green-50 text-green-800 border-green-200" },
  STALE: { label: "Out of date", cls: "bg-amber-50 text-amber-800 border-amber-200" },
};

export function AssessmentStatusBadge({ status }: { status: AssessmentStatus }) {
  const s = STATUS[status];
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", s.cls)}>{s.label}</span>;
}
