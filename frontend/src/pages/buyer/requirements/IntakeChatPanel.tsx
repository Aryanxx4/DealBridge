import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { PriorityBadge } from "@/components/shared/Badges";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { cn } from "@/lib/utils";
import { assessmentsApi } from "@/services/assessments";
import { type Assessment, CATEGORY_LABELS, type ChangeProposal } from "@/types/api";

export function IntakeChatPanel({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [draft, setDraft] = useState("");
  const q = useQuery({ queryKey: ["intake", userKey, assessment.id], queryFn: () => assessmentsApi.intake(assessment.id) });
  const send = useMutation({
    mutationFn: (content: string) => assessmentsApi.sendIntake(assessment.id, content),
    onSuccess: () => {
      setDraft("");
      qc.invalidateQueries({ queryKey: ["intake", userKey, assessment.id] });
    },
    onError: (e: Error) => {
      toast.error(e.message);
      qc.invalidateQueries({ queryKey: ["intake", userKey, assessment.id] });
    },
  });
  const byMessage = new Map((q.data?.proposals ?? []).map((p) => [p.message_id, p]));
  const submit = () => draft.trim() && !send.isPending && send.mutate(draft.trim());
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Describe your needs in your own words. Proposed changes appear as cards; nothing changes until you click Apply.</p>
      {q.isLoading && <LoadingRows rows={2} />}
      {q.error && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      <div className="max-h-[28rem] space-y-3 overflow-y-auto" aria-live="polite">
        {q.data?.messages.map((m) =>
          m.role === "USER" ? (
            <div key={m.id} className="flex justify-end"><p className="max-w-[80%] whitespace-pre-wrap rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">{m.content}</p></div>
          ) : (
            <div key={m.id} className="space-y-2">
              <div className="max-w-[90%] rounded-lg border bg-slate-50 p-3 text-sm">
                <p className="whitespace-pre-wrap">{m.content}</p>
                {!!m.structured?.clarifying_questions?.length && (
                  <ul className="mt-2 list-disc pl-5 text-slate-700">{m.structured.clarifying_questions.map((c) => <li key={c}>{c}</li>)}</ul>
                )}
              </div>
              {byMessage.get(m.id) && <ProposalCard assessment={assessment} p={byMessage.get(m.id)!} />}
            </div>
          ),
        )}
        {send.isPending && (
          <div className="max-w-[90%] space-y-2 rounded-lg border bg-slate-50 p-3" aria-busy="true">
            <p className="text-sm text-muted-foreground">Reading your message…</p>
            <Skeleton className="h-3 w-2/3" />
          </div>
        )}
      </div>
      <div className="flex items-end gap-2">
        <label htmlFor="intake-input" className="sr-only">Describe your requirements</label>
        <Textarea id="intake-input" rows={2} maxLength={4000} value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }} placeholder="e.g. We need a self-hosted platform and our data cannot leave our infrastructure." />
        <Button onClick={submit} disabled={!draft.trim() || send.isPending} aria-label="Send"><Send aria-hidden /></Button>
      </div>
    </div>
  );
}

function ProposalCard({ assessment, p }: { assessment: Assessment; p: ChangeProposal }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<number[]>(p.ops.map((_, i) => i));
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["intake", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["requirements", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
  };
  const apply = useMutation({ mutationFn: () => assessmentsApi.applyProposal(assessment.id, p.id, selected), onSuccess: (r) => { toast.success(`${r.changed.length} change(s) applied`); refresh(); }, onError: (e: Error) => { toast.error(e.message); refresh(); } });
  const dismiss = useMutation({ mutationFn: () => assessmentsApi.dismissProposal(assessment.id, p.id), onSuccess: refresh, onError: (e: Error) => toast.error(e.message) });

  if (p.status !== "PENDING") {
    return (
      <div className="ml-4 rounded-md border bg-card p-2 text-xs text-muted-foreground">
        {p.status === "APPLIED" ? (
          <span className="inline-flex items-center gap-1"><CheckCircle2 className="size-3.5 text-green-700" aria-hidden /> Applied: {p.result?.changed.map((c) => `${c.op.toLowerCase()} ${c.display_id}`).join(", ")}</span>
        ) : "Dismissed"}
      </div>
    );
  }
  return (
    <div className="ml-4 space-y-2 rounded-lg border border-indigo-200 bg-card p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800">Proposed changes</p>
      {p.ops.map((op, i) => (
        <label key={i} className={cn("flex cursor-pointer items-start gap-2 rounded-md border p-2 text-sm", op.op === "ADD" && "border-green-200 bg-green-50", op.op === "REMOVE" && "border-red-200 bg-red-50", op.op === "UPDATE" && "border-blue-200 bg-blue-50")}>
          <Checkbox checked={selected.includes(i)} onCheckedChange={(c) => setSelected((s) => (c ? [...s, i] : s.filter((x) => x !== i)))} aria-label={`Include change ${i + 1}`} />
          <div className="min-w-0 space-y-1">
            <p className="text-xs font-semibold">{op.op === "ADD" ? "Add" : op.op === "REMOVE" ? `Remove ${op.target_display_id}` : `Update ${op.target_display_id}`}</p>
            {op.op === "REMOVE" && <p className="line-through">{op.target_snapshot?.normalized_text}</p>}
            {op.op === "UPDATE" && (
              <p><span className="line-through text-slate-500">{op.target_snapshot?.normalized_text}</span> → <span>{op.normalized_text ?? "(unchanged text)"}</span></p>
            )}
            {op.op === "ADD" && <p>{op.normalized_text}</p>}
            <div className="flex flex-wrap gap-2 text-xs">
              {op.category && <span className="text-muted-foreground">{CATEGORY_LABELS[op.category]}</span>}
              {op.priority && <PriorityBadge priority={op.priority} />}
              <span className="italic text-muted-foreground">“{op.source_quote}”</span>
            </div>
          </div>
        </label>
      ))}
      <div className="flex gap-2">
        <Button size="sm" onClick={() => apply.mutate()} disabled={!selected.length || apply.isPending}>Apply selected</Button>
        <Button size="sm" variant="outline" onClick={() => dismiss.mutate()} disabled={dismiss.isPending}>Dismiss</Button>
      </div>
    </div>
  );
}
