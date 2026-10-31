import { AlertTriangle, Inbox, RotateCw } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/services/api";

export function EmptyState({ title, description, action, icon }: { title: string; description?: string; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 py-12 text-center">
      <div className="mb-3 text-slate-400">{icon ?? <Inbox className="size-8" aria-hidden />}</div>
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, onRetry, title = "Something went wrong" }: { error: unknown; onRetry?: () => void; title?: string }) {
  const e = error instanceof ApiError ? error : null;
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red-700" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-semibold">{title}</p>
          <p className="mt-1">{e?.message ?? (error instanceof Error ? error.message : "Unexpected error.")}</p>
          {e && (
            <p className="mt-1 text-xs text-red-800/80">
              Code: {e.code}
              {e.requestId ? ` · Request ID: ${e.requestId}` : ""}
            </p>
          )}
        </div>
        {onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry}>
            <RotateCw aria-hidden /> Retry
          </Button>
        )}
      </div>
    </div>
  );
}

export function LoadingRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );
}
