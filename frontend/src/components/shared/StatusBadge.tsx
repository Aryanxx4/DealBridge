import { CheckCircle2, CircleDot, HelpCircle, SearchCheck, XCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { FitStatus } from "@/types/api";

export const STATUS_META: Record<FitStatus, { label: string; cls: string; Icon: typeof CheckCircle2; definition: string }> = {
  SUPPORTED: { label: "Supported", cls: "bg-green-50 text-green-700 border-green-200", Icon: CheckCircle2, definition: "Reliable evidence directly supports the requirement." },
  PARTIALLY_SUPPORTED: { label: "Partially supported", cls: "bg-amber-50 text-amber-800 border-amber-200", Icon: CircleDot, definition: "Evidence supports only part of the requirement or describes material limitations." },
  NEEDS_VALIDATION: { label: "Needs validation", cls: "bg-blue-50 text-blue-800 border-blue-200", Icon: SearchCheck, definition: "A related capability exists, but buyer-specific details or technical confirmation are needed." },
  NOT_SUPPORTED: { label: "Not supported", cls: "bg-red-50 text-red-800 border-red-200", Icon: XCircle, definition: "Reliable, current evidence indicates a mismatch." },
  UNKNOWN: { label: "Unknown", cls: "bg-slate-100 text-slate-700 border-slate-300", Icon: HelpCircle, definition: "There is insufficient reliable evidence to reach a conclusion." },
};

/** Always an icon plus a text label (never colour alone), with the status definition as a tooltip. */
export function StatusBadge({ status, className }: { status: FitStatus; className?: string }) {
  const s = STATUS_META[status];
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span tabIndex={0} className={cn("inline-flex cursor-help items-center gap-1 whitespace-nowrap rounded-md border px-2 py-0.5 text-xs font-medium", s.cls, className)}>
          <s.Icon className="size-3.5" aria-hidden />
          {s.label}
        </span>
      </TooltipTrigger>
      <TooltipContent>{s.definition}</TooltipContent>
    </Tooltip>
  );
}

export const STATUS_ORDER: FitStatus[] = ["SUPPORTED", "PARTIALLY_SUPPORTED", "NEEDS_VALIDATION", "NOT_SUPPORTED", "UNKNOWN"];
