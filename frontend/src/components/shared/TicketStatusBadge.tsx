import { cn } from "@/lib/utils";
import type { TicketStatus } from "@/types/api";

const MAP: Record<TicketStatus, { label: string; cls: string }> = {
  OPEN: { label: "Open", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  IN_REVIEW: { label: "In review", cls: "bg-amber-50 text-amber-800 border-amber-200" },
  ANSWER_PROPOSED: { label: "Answer proposed", cls: "bg-violet-50 text-violet-800 border-violet-200" },
  APPROVED: { label: "Approved", cls: "bg-green-50 text-green-800 border-green-200" },
  REJECTED: { label: "Rejected", cls: "bg-red-50 text-red-800 border-red-200" },
  PUBLISHED: { label: "Answered", cls: "bg-green-50 text-green-800 border-green-200" },
  CLOSED: { label: "Closed", cls: "bg-slate-100 text-slate-700 border-slate-200" },
};

export function TicketStatusBadge({ status }: { status: TicketStatus }) {
  const s = MAP[status];
  return <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", s.cls)}>{s.label}</span>;
}
