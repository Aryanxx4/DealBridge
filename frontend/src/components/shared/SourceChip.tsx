import { BookOpen, BadgeCheck, Building2, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";

export type SourceKind = "official" | "expert" | "seller" | "general";

const STYLE: Record<SourceKind, { label: string; cls: string; Icon: typeof BookOpen }> = {
  official: { label: "Official documentation", cls: "bg-indigo-50 text-indigo-800 border-indigo-200", Icon: BookOpen },
  expert: { label: "Expert-verified answer", cls: "bg-violet-50 text-violet-800 border-violet-200", Icon: BadgeCheck },
  seller: { label: "Seller statement", cls: "bg-teal-50 text-teal-800 border-teal-200", Icon: Building2 },
  general: { label: "General explanation", cls: "bg-slate-100 text-slate-700 border-slate-200", Icon: Lightbulb },
};

export function SourceChip({ kind, className }: { kind: SourceKind; className?: string }) {
  const s = STYLE[kind];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", s.cls, className)}>
      <s.Icon className="size-3.5" aria-hidden />
      {s.label}
    </span>
  );
}

export function kindOf(collection: "OFFICIAL" | "RESOLVED"): SourceKind {
  return collection === "OFFICIAL" ? "official" : "expert";
}
