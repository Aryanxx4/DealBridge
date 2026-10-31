import { Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import type { Job } from "@/types/api";

export function JobProgress({ job, label }: { job: Job | undefined; label: string }) {
  const total = job?.progress_total ?? 0;
  const pct = total > 0 ? Math.round(((job?.progress_done ?? 0) / total) * 100) : undefined;
  return (
    <div className="rounded-lg border bg-card p-4" aria-live="polite">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Loader2 className="size-4 animate-spin text-primary" aria-hidden />
        {label}
      </div>
      <Progress className="mt-3" value={pct ?? 5} aria-label={`${label} progress`} />
      <p className="mt-2 text-xs text-muted-foreground">
        {job?.progress_message ?? (job?.status === "QUEUED" ? "Queued…" : "Starting…")}
        {pct !== undefined && ` · ${job?.progress_done} of ${total}`}
      </p>
    </div>
  );
}
