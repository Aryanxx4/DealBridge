import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useIdentity, useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { sharingApi } from "@/services/sharing";
import type { FollowUp, FollowUpStatus } from "@/types/api";

const STATUS: Record<FollowUpStatus, { label: string; cls: string }> = {
  REQUESTED: { label: "Requested", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  IN_PROGRESS: { label: "In progress", cls: "bg-amber-50 text-amber-800 border-amber-200" },
  RESPONDED: { label: "Responded", cls: "bg-green-50 text-green-800 border-green-200" },
  CLOSED: { label: "Closed", cls: "bg-slate-100 text-slate-700 border-slate-200" },
};

export function FollowUpStatusBadge({ status }: { status: FollowUpStatus }) {
  return <span className={cn("rounded-md border px-2 py-0.5 text-xs font-medium", STATUS[status].cls)}>{STATUS[status].label}</span>;
}

export function FollowUpThread({ id }: { id: string }) {
  const { user } = useIdentity();
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [draft, setDraft] = useState("");
  const q = useQuery({ queryKey: ["follow-up", userKey, id], queryFn: () => sharingApi.followUp(id) });
  const done = (f: FollowUp) => {
    qc.setQueryData(["follow-up", userKey, id], f);
    qc.invalidateQueries({ queryKey: ["follow-ups", userKey] });
    setDraft("");
  };
  const act = useMutation({ mutationFn: (fn: () => Promise<FollowUp>) => fn(), onSuccess: done, onError: (e: Error) => toast.error(e.message) });
  if (q.isLoading) return <LoadingRows rows={3} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const f = q.data!;
  const isSeller = user?.role === "SELLER";
  const can = (a: string) => f.allowed_actions.includes(a);
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">{f.subject}</h3>
        <FollowUpStatusBadge status={f.status} />
        <span className="text-xs text-muted-foreground">{f.buyer_org} ↔ {f.seller_org} · opened {formatDateTime(f.created_at)}</span>
      </div>
      {f.decision_reason && <p className="rounded-md bg-slate-50 p-2 text-sm">Seller decision: {f.seller_decision.toLowerCase()} — {f.decision_reason}</p>}
      <ol className="space-y-2" aria-live="polite">
        {f.messages?.map((m) => (
          <li key={m.id} className={cn("max-w-[85%] rounded-lg border p-3 text-sm", m.author_role === "SELLER" ? "border-teal-200 bg-teal-50/60" : "ml-auto bg-slate-50")}>
            <p className="text-xs text-muted-foreground">{m.author} · {m.author_org} · {formatDateTime(m.created_at)}</p>
            <p className="mt-1 whitespace-pre-wrap">{m.body}</p>
          </li>
        ))}
        {!f.messages?.length && <p className="text-sm text-muted-foreground">No messages yet.</p>}
      </ol>
      {f.status !== "CLOSED" && (
        <div className="space-y-2">
          <label htmlFor={`fu-${id}`} className="sr-only">Message</label>
          <Textarea id={`fu-${id}`} rows={3} maxLength={4000} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={isSeller ? "Write a response to the buyer…" : "Add information for the seller…"} />
          <div className="flex flex-wrap gap-2">
            {isSeller && can("accept") && <Button variant="outline" onClick={() => act.mutate(() => sharingApi.accept(id))}>Accept</Button>}
            {isSeller && can("respond") && <Button disabled={!draft.trim()} onClick={() => act.mutate(() => sharingApi.respond(id, draft.trim()))}>Respond</Button>}
            {!isSeller && <Button disabled={!draft.trim()} onClick={() => act.mutate(() => sharingApi.buyerMessage(id, draft.trim()))}>Send</Button>}
            {isSeller && can("reject") && (
              <ConfirmDialog trigger={<Button variant="outline" className="text-red-700">Reject</Button>} title="Reject this follow-up?" description="The thread is closed and the buyer sees your reason." confirmLabel="Reject" destructive reasonLabel="Reason (required)" onConfirm={(r) => act.mutateAsync(() => sharingApi.reject(id, r))} />
            )}
            <ConfirmDialog trigger={<Button variant="ghost">Close thread</Button>} title="Close this follow-up?" description="A closed thread becomes read-only." confirmLabel="Close" onConfirm={() => act.mutateAsync(() => sharingApi.close(id))} />
          </div>
        </div>
      )}
    </div>
  );
}
