import { useQuery } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Markdown } from "@/components/shared/Markdown";
import { SourceChip } from "@/components/shared/SourceChip";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { TicketStatusBadge } from "@/components/shared/TicketStatusBadge";
import { Button } from "@/components/ui/button";
import { useIdentity, useUserKey } from "@/hooks/useIdentity";
import { formatDate, formatDateTime } from "@/lib/utils";
import { myQuestionsApi } from "@/services/admin";

export function MyQuestionsPage() {
  const { user } = useIdentity();
  const userKey = useUserKey();
  const q = useQuery({ queryKey: ["my-tickets", userKey], queryFn: myQuestionsApi.list, enabled: !!user, refetchInterval: 15_000 });
  const [open, setOpen] = useState<string | null>(null);
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">My questions</h1>
        <p className="text-sm text-muted-foreground">Questions the product chat could not verify, raised with the product team. Approved answers appear here.</p>
      </div>
      {q.isLoading && <LoadingRows rows={4} />}
      {q.error && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data?.length === 0 && (
        <EmptyState
          title="No open questions"
          description="When the chat can't verify an answer, the question is raised with the product team and tracked here."
          action={
            <Button asChild variant="outline">
              <Link to="/chat">Open product chat</Link>
            </Button>
          }
        />
      )}
      <ul className="space-y-2">
        {q.data?.map((t) => (
          <li key={t.id} className="rounded-lg border bg-card">
            <button
              type="button"
              className="flex w-full flex-wrap items-center gap-3 p-4 text-left"
              onClick={() => setOpen(open === t.id ? null : t.id)}
              aria-expanded={open === t.id}
              disabled={!t.answer}
            >
              <span className="font-mono text-xs text-muted-foreground">{t.display_id}</span>
              <span className="min-w-0 flex-1 font-medium">{t.question}</span>
              <TicketStatusBadge status={t.status} />
              <span className="text-xs text-muted-foreground">{formatDateTime(t.created_at)}</span>
              {t.occurrence_count > 1 && <span className="text-xs text-muted-foreground">asked {t.occurrence_count}×</span>}
              {t.answer && <ChevronDown className="size-4 text-muted-foreground" aria-hidden />}
            </button>
            {t.answer && open === t.id && (
              <div className="border-t bg-violet-50/40 p-4 text-sm">
                <div className="mb-2 flex items-center gap-2">
                  <SourceChip kind="expert" />
                  <span className="text-xs text-muted-foreground">
                    Approved {formatDate(t.answer.approved_at)} · version {t.answer.version}
                  </span>
                </div>
                <Markdown text={t.answer.text} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
