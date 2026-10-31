import { AlertCircle, BadgeCheck, BookOpen, CircleHelp, Layers, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnswerType } from "@/types/api";

const MAP: Partial<Record<AnswerType, { label: string; cls: string; Icon: typeof BookOpen }>> = {
  OFFICIAL_VERIFIED: { label: "Verified from official documentation", cls: "bg-indigo-50 text-indigo-800 border-indigo-200", Icon: BookOpen },
  EXPERT_VERIFIED: { label: "Expert-verified answer", cls: "bg-violet-50 text-violet-800 border-violet-200", Icon: BadgeCheck },
  MIXED_VERIFIED: { label: "Official documentation and expert-verified answer", cls: "bg-indigo-50 text-indigo-800 border-indigo-200", Icon: Layers },
  GENERAL_EXPLANATION: { label: "General explanation — not specific to IOMETE", cls: "bg-slate-100 text-slate-700 border-slate-200", Icon: Lightbulb },
  PARTIAL: { label: "Partly verified", cls: "bg-amber-50 text-amber-800 border-amber-200", Icon: CircleHelp },
  UNVERIFIED: { label: "Could not verify", cls: "bg-slate-100 text-slate-800 border-slate-300", Icon: AlertCircle },
};

export function AnswerTypeBadge({ type }: { type: AnswerType | null }) {
  const s = type ? MAP[type] : undefined;
  if (!s) return null;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", s.cls)}>
      <s.Icon className="size-3.5" aria-hidden />
      {s.label}
    </span>
  );
}
