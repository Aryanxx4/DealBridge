import type { Assessment } from "@/types/api";
import { useRequirements } from "./ReviewTable";

export function RequirementsFooter({ assessment }: { assessment: Assessment }) {
  const q = useRequirements(assessment.id, false);
  const rows = q.data ?? [];
  const confirmed = rows.filter((r) => r.buyer_confirmed).length;
  const clarify = rows.filter((r) => r.needs_clarification && !r.clarification_waived).length;
  return (
    <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-card/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-sm">
        <span><strong className="tabular-nums">{rows.length}</strong> active</span>
        <span><strong className="tabular-nums">{confirmed}</strong> confirmed</span>
        <span><strong className="tabular-nums">{rows.length - confirmed}</strong> unconfirmed</span>
        {clarify > 0 && <span className="text-amber-800"><strong className="tabular-nums">{clarify}</strong> need clarification</span>}
      </div>
    </div>
  );
}
