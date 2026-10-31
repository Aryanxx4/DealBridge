import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Controller, useFieldArray, useForm, useWatch } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";
import { RequireRole } from "@/components/layout/RequireRole";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Markdown } from "@/components/shared/Markdown";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { TicketStatusBadge } from "@/components/shared/TicketStatusBadge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { formatDateTime } from "@/lib/utils";
import { adminApi } from "@/services/admin";
import { ApiError } from "@/services/api";
import type { TicketDetail } from "@/types/api";

const CATEGORIES = ["deployment", "architecture", "security", "platform", "integrations", "concepts", "OTHER"];

const answerSchema = z.object({
  normalised_question: z.string().trim().min(5, "At least 5 characters").max(1000),
  category: z.string(),
  answer: z.string().trim().min(40, "The answer must be at least 40 characters").max(8000),
  supporting_sources: z.array(
    z.object({ title: z.string().trim().min(1, "Title required"), url: z.union([z.literal(""), z.string().url("Must be a URL")]), note: z.string().optional() }),
  ),
  internal_notes: z.string().optional(),
  privacy_confirmed: z.literal(true, { message: "Confirm the privacy statement before submitting" }),
});
type AnswerForm = z.input<typeof answerSchema>;

export function TicketDetailPage() {
  return (
    <RequireRole roles={["ADMIN"]}>
      <TicketDetailInner />
    </RequireRole>
  );
}

function TicketDetailInner() {
  const { id = "" } = useParams();
  const userKey = useUserKey();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-ticket", userKey, id], queryFn: () => adminApi.ticket(id) });
  const refresh = (t?: TicketDetail) => {
    if (t) qc.setQueryData(["admin-ticket", userKey, id], t);
    qc.invalidateQueries({ queryKey: ["admin-tickets", userKey] });
    qc.invalidateQueries({ queryKey: ["admin-dashboard", userKey] });
  };
  const act = useMutation({
    mutationFn: ({ action, body }: { action: string; body?: Record<string, unknown> }) => adminApi.action(id, action, body),
    onSuccess: (t, v) => {
      refresh(t);
      toast.success(v.action === "approve" ? `Approved and published (${t.display_id})` : "Ticket updated");
    },
    onError: (e) => {
      toast.error(e instanceof ApiError ? `${e.message} (${e.code})` : String(e));
      qc.invalidateQueries({ queryKey: ["admin-ticket", userKey, id] });
    },
  });

  if (q.isLoading) return <LoadingRows rows={6} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const t = q.data!;
  const can = (a: string) => t.allowed_actions.includes(a);

  return (
    <div className="space-y-4">
      <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" aria-hidden /> Back to queue
      </Link>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="font-mono text-xl font-semibold">{t.display_id}</h1>
        <TicketStatusBadge status={t.status} />
        <span className="text-sm text-muted-foreground">
          Asked {t.occurrence_count}× · priority {t.priority.toLowerCase()} · reason {t.reason.replaceAll("_", " ").toLowerCase()}
          {t.assigned_to ? ` · assigned to ${t.assigned_to}` : ""}
        </span>
      </div>
      {t.publish_error && (
        <Alert variant="destructive">
          <AlertTriangle aria-hidden />
          <AlertTitle>Approved, but indexing failed</AlertTitle>
          <AlertDescription>
            {t.publish_error}
            <div className="mt-2">
              <Button size="sm" onClick={() => act.mutate({ action: "publish" })} disabled={act.isPending}>
                Retry publishing
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}
      <div className="grid gap-4 lg:grid-cols-[1fr_22rem]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Question</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-xs font-medium uppercase text-muted-foreground">Normalised (customer-neutral)</p>
                <p className="mt-1">{t.normalised_question}</p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase text-muted-foreground">Original wording (internal only)</p>
                <p className="mt-1 text-slate-700">{t.original_question}</p>
              </div>
              {t.occurrences.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase text-muted-foreground">Also asked</p>
                  <ul className="mt-1 list-disc pl-5">
                    {t.occurrences.map((o, i) => (
                      <li key={i}>
                        {o.question_text} <span className="text-xs text-muted-foreground">({formatDateTime(o.created_at)})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
          {t.context_excerpt.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Conversation context</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <Alert variant="warning">
                  <AlertTriangle aria-hidden />
                  <AlertDescription>Buyer-provided context. Do not copy it into published answers.</AlertDescription>
                </Alert>
                {t.context_excerpt.map((m, i) => (
                  <p key={i} className="rounded-md bg-slate-50 p-2">
                    <span className="mr-2 text-xs font-semibold uppercase text-muted-foreground">{m.role.toLowerCase()}</span>
                    {m.content}
                  </p>
                ))}
              </CardContent>
            </Card>
          )}
          <TraceCard t={t} />
          {can("answer") && <AnswerEditor t={t} onSaved={refresh} />}
          {t.proposed_answer && !can("answer") && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Proposed answer</CardTitle>
                <p className="text-xs text-muted-foreground">
                  by {t.proposed_by} · {formatDateTime(t.proposed_at)}
                  {t.published_version ? ` · published as version ${t.published_version}` : ""}
                </p>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <Markdown text={t.proposed_answer} />
                {t.supporting_sources.length > 0 && (
                  <ul className="list-disc pl-5 text-xs">
                    {t.supporting_sources.map((s, i) => (
                      <li key={i}>
                        {s.url ? (
                          <a href={s.url} target="_blank" rel="noopener noreferrer">
                            {s.title}
                          </a>
                        ) : (
                          s.title
                        )}
                        {s.note ? ` — ${s.note}` : ""}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          )}
        </div>
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {t.reviewer_note && <p className="rounded-md bg-amber-50 p-2 text-xs text-amber-900">Reviewer note: {t.reviewer_note}</p>}
            {can("start-review") && (
              <Button className="w-full" onClick={() => act.mutate({ action: "start-review" })} disabled={act.isPending}>
                Start review
              </Button>
            )}
            {can("approve") && (
              <ConfirmDialog
                trigger={<Button className="w-full">Approve and publish</Button>}
                title="Approve and publish this answer?"
                description="It will be embedded into the expert-answer knowledge base and reused for matching questions, labelled 'Expert-verified answer'."
                confirmLabel="Approve and publish"
                onConfirm={() => act.mutateAsync({ action: "approve" })}
              />
            )}
            {can("publish") && t.status === "APPROVED" && !t.publish_error && (
              <Button className="w-full" onClick={() => act.mutate({ action: "publish" })}>
                Publish
              </Button>
            )}
            {can("request-revision") && (
              <ConfirmDialog trigger={<Button variant="outline" className="w-full">Request revision</Button>} title="Request a revision" description="The ticket returns to In review." confirmLabel="Request revision" reasonLabel="Reviewer note (required)" onConfirm={(r) => act.mutateAsync({ action: "request-revision", body: { reviewer_note: r } })} />
            )}
            {can("reopen") && (
              <Button variant="outline" className="w-full" onClick={() => act.mutate({ action: "reopen" })}>
                Reopen
              </Button>
            )}
            {can("reject") && (
              <ConfirmDialog trigger={<Button variant="outline" className="w-full text-red-700">Reject</Button>} title="Reject this ticket's answer?" description="A rejected answer is never indexed." confirmLabel="Reject" destructive reasonLabel="Reviewer note (required)" onConfirm={(r) => act.mutateAsync({ action: "reject", body: { reviewer_note: r } })} />
            )}
            {can("close") && <CloseDialog onClose={(body) => act.mutateAsync({ action: "close", body })} />}
            {t.allowed_actions.length === 0 && <p className="text-sm text-muted-foreground">No further actions. This ticket is {t.status.toLowerCase()}.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TraceCard({ t }: { t: TicketDetail }) {
  const tr = t.retrieval_trace;
  if (!tr) return null;
  return (
    <Card>
      <CardContent className="pt-2">
        <Accordion type="single" collapsible>
          <AccordionItem value="trace" className="border-b-0">
            <AccordionTrigger>Retrieval trace ({tr.hits?.length ?? 0} hits)</AccordionTrigger>
            <AccordionContent className="space-y-3">
              <p className="text-xs text-muted-foreground">
                Decision: <strong>{tr.decision ?? "—"}</strong>
                {tr.thresholds && ` · thresholds ${Object.entries(tr.thresholds).map(([k, v]) => `${k}=${v}`).join(", ")}`}
                {tr.classification && ` · intent ${String(tr.classification.intent)}`}
              </p>
              <p className="text-xs text-muted-foreground">Scores are retrieval signals for debugging, not evidence.</p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Collection</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(tr.hits ?? []).map((h) => (
                    <TableRow key={`${h.collection}-${h.chunk_id}`}>
                      <TableCell className="text-xs">{h.collection.toLowerCase()}</TableCell>
                      <TableCell className="max-w-md">
                        <p className="truncate text-xs font-medium">{h.heading_path}</p>
                        <p className="line-clamp-2 text-xs text-muted-foreground">{h.excerpt}</p>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">{h.score.toFixed(3)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}

function AnswerEditor({ t, onSaved }: { t: TicketDetail; onSaved: (t: TicketDetail) => void }) {
  const form = useForm<AnswerForm>({
    resolver: zodResolver(answerSchema),
    defaultValues: {
      normalised_question: t.normalised_question,
      category: CATEGORIES.includes(t.category) ? t.category : "OTHER",
      answer: t.proposed_answer ?? "",
      supporting_sources: t.supporting_sources.map((s) => ({ title: s.title, url: s.url ?? "", note: s.note ?? "" })),
      internal_notes: t.internal_notes ?? "",
      privacy_confirmed: false as unknown as true,
    },
  });
  const sources = useFieldArray({ control: form.control, name: "supporting_sources" });
  const answer = useWatch({ control: form.control, name: "answer" });
  const save = useMutation({
    mutationFn: (v: AnswerForm) =>
      adminApi.answer(t.id, {
        normalised_question: v.normalised_question,
        category: v.category,
        answer: v.answer,
        supporting_sources: v.supporting_sources.map((s) => ({ title: s.title, url: s.url || null, note: s.note || null })),
        internal_notes: v.internal_notes || null,
        privacy_confirmed: v.privacy_confirmed === true,
      }),
    onSuccess: (res) => {
      onSaved(res);
      toast.success("Answer submitted for approval");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const err = form.formState.errors;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Propose an answer</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={form.handleSubmit((v) => save.mutate(v))} noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="nq">Normalised question (customer-neutral)</Label>
            <Textarea id="nq" rows={2} {...form.register("normalised_question")} />
            {err.normalised_question && <p className="text-xs text-red-700">{err.normalised_question.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label>Category</Label>
            <Controller
              control={form.control}
              name="category"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className="w-56" aria-label="Category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="ans">Answer (Markdown)</Label>
              <Textarea id="ans" rows={9} {...form.register("answer")} />
              {err.answer && <p className="text-xs text-red-700">{err.answer.message}</p>}
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Preview</p>
              <div className="min-h-[13rem] rounded-md border bg-slate-50 p-3 text-sm">{answer ? <Markdown text={answer} /> : <span className="text-muted-foreground">Nothing to preview yet.</span>}</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Supporting sources</Label>
              <Button type="button" size="sm" variant="outline" onClick={() => sources.append({ title: "", url: "", note: "" })}>
                <Plus aria-hidden /> Add source
              </Button>
            </div>
            {sources.fields.map((f, i) => (
              <div key={f.id} className="grid gap-2 rounded-md border p-2 md:grid-cols-[1fr_1fr_1fr_auto]">
                <Input placeholder="Title" aria-label={`Source ${i + 1} title`} {...form.register(`supporting_sources.${i}.title`)} />
                <Input placeholder="https://…" aria-label={`Source ${i + 1} URL`} {...form.register(`supporting_sources.${i}.url`)} />
                <Input placeholder="Note" aria-label={`Source ${i + 1} note`} {...form.register(`supporting_sources.${i}.note`)} />
                <Button type="button" size="icon" variant="ghost" aria-label={`Remove source ${i + 1}`} onClick={() => sources.remove(i)}>
                  <Trash2 aria-hidden />
                </Button>
                {err.supporting_sources?.[i] && <p className="text-xs text-red-700 md:col-span-4">{err.supporting_sources[i]?.title?.message ?? err.supporting_sources[i]?.url?.message}</p>}
              </div>
            ))}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notes">Internal notes (never published)</Label>
            <Textarea id="notes" rows={2} {...form.register("internal_notes")} />
          </div>
          <Controller
            control={form.control}
            name="privacy_confirmed"
            render={({ field }) => (
              <div className="flex items-start gap-2">
                <Checkbox id="privacy" checked={field.value === true} onCheckedChange={(c) => field.onChange(c === true)} />
                <Label htmlFor="privacy" className="leading-snug">
                  This answer contains no buyer-private or customer-specific information
                </Label>
              </div>
            )}
          />
          {err.privacy_confirmed && <p className="text-xs text-red-700">{err.privacy_confirmed.message}</p>}
          <Button type="submit" disabled={save.isPending}>
            Submit for approval
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function CloseDialog({ onClose }: { onClose: (body: Record<string, unknown>) => Promise<unknown> }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("OUT_OF_SCOPE");
  const [busy, setBusy] = useState(false);
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" className="w-full">
          Close ticket…
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Close this ticket?</DialogTitle>
          <DialogDescription>Closed tickets are not answered and are never indexed.</DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label>Reason</Label>
          <Select value={reason} onValueChange={setReason}>
            <SelectTrigger aria-label="Close reason">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DUPLICATE">Duplicate</SelectItem>
              <SelectItem value="OUT_OF_SCOPE">Out of scope</SelectItem>
              <SelectItem value="NOT_A_PRODUCT_QUESTION">Not a product question</SelectItem>
              <SelectItem value="OTHER">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await onClose({ reason });
                setOpen(false);
              } finally {
                setBusy(false);
              }
            }}
          >
            Close ticket
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
