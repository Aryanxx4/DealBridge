import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, FileText, History, MessageSquare, PenLine, Plus, RotateCcw, ListChecks, Trash2, Keyboard } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { ApiError } from "@/services/api";
import { assessmentsApi, requirementsApi } from "@/services/assessments";
import { type Assessment, CATEGORY_LABELS, PRIORITY_LABELS, type Priority, type Requirement, type RequirementCategory } from "@/types/api";

const CATEGORIES = Object.keys(CATEGORY_LABELS) as RequirementCategory[];
const PRIORITIES = Object.keys(PRIORITY_LABELS) as Priority[];

export function useRequirements(assessmentId: string, includeRemoved: boolean) {
  const userKey = useUserKey();
  return useQuery({ queryKey: ["requirements", userKey, assessmentId, includeRemoved], queryFn: () => assessmentsApi.requirements(assessmentId, includeRemoved) });
}

export function ReviewTable({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [showRemoved, setShowRemoved] = useState(false);
  const q = useRequirements(assessment.id, showRemoved);
  const locked = assessment.status === "ANALYZING";
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["requirements", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
  };
  const onError = (e: unknown) => toast.error(e instanceof ApiError ? e.message : String(e));
  const mut = useMutation({
    mutationFn: ({ fn }: { fn: () => Promise<unknown> }) => fn(),
    onSuccess: refresh,
    onError: (e) => {
      onError(e);
      refresh();
    },
  });
  const confirmAll = useMutation({
    mutationFn: () => assessmentsApi.confirmAll(assessment.id),
    onSuccess: (r) => { toast.success(r.confirmed.length ? `Confirmed ${r.confirmed.length} requirement(s)` : "Nothing to confirm (requirements that need clarification are skipped)"); refresh(); },
    onError,
  });

  if (q.isLoading) return <LoadingRows rows={4} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const rows = q.data ?? [];
  const active = rows.filter((r) => !r.is_removed);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Review requirements</h2>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Checkbox id="show-removed" checked={showRemoved} onCheckedChange={(c) => setShowRemoved(c === true)} />
            <Label htmlFor="show-removed" className="text-sm font-normal">Show removed</Label>
          </div>
          <Button variant="outline" size="sm" onClick={() => confirmAll.mutate()} disabled={locked || confirmAll.isPending || !active.some((r) => !r.buyer_confirmed)}>
            <ListChecks aria-hidden /> Confirm all
          </Button>
        </div>
      </div>
      {locked && <p className="text-sm text-blue-800">An assessment is running. Requirements are locked until it finishes.</p>}
      {rows.length === 0 ? (
        <EmptyState title="No requirements yet" description="Upload a PDF, chat, or use the guided form above, or add one directly below." />
      ) : (
        <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-20">ID</TableHead>
                <TableHead>Requirement</TableHead>
                <TableHead className="w-48">Category</TableHead>
                <TableHead className="w-36">Priority</TableHead>
                <TableHead className="w-20">Source</TableHead>
                <TableHead className="w-44">State</TableHead>
                <TableHead className="w-28">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => (
                <Row key={r.id} r={r} locked={locked} run={(fn) => mut.mutate({ fn })} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      {!locked && <AddRow assessment={assessment} onAdded={refresh} />}
    </div>
  );
}

function Row({ r, locked, run }: { r: Requirement; locked: boolean; run: (fn: () => Promise<unknown>) => void }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(r.normalized_text);
  const disabled = locked || r.is_removed;
  return (
    <TableRow className={cn("align-top", r.is_removed && "bg-slate-50 text-muted-foreground")}>
      <TableCell className="font-mono text-xs">{r.display_id}</TableCell>
      <TableCell className="min-w-[16rem]">
        {editing ? (
          <div className="space-y-2">
            <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} aria-label={`Edit ${r.display_id}`} />
            <div className="flex gap-2">
              <Button size="sm" disabled={text.trim().length < 5 || text.trim().length > 1000} onClick={() => { run(() => requirementsApi.patch(r.id, { normalized_text: text.trim() })); setEditing(false); }}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => { setText(r.normalized_text); setEditing(false); }}>Cancel</Button>
            </div>
          </div>
        ) : (
          <p className={cn(r.is_removed && "line-through")}>{r.normalized_text}</p>
        )}
        {r.original_text !== r.normalized_text && !editing && <p className="mt-1 text-xs italic text-muted-foreground">Original: “{r.original_text}”</p>}
      </TableCell>
      <TableCell>
        <Select value={r.category} disabled={disabled} onValueChange={(v) => run(() => requirementsApi.patch(r.id, { category: v as RequirementCategory }))}>
          <SelectTrigger className="h-8 text-xs" aria-label={`${r.display_id} category`}><SelectValue /></SelectTrigger>
          <SelectContent>{CATEGORIES.map((c) => <SelectItem key={c} value={c}>{CATEGORY_LABELS[c]}</SelectItem>)}</SelectContent>
        </Select>
      </TableCell>
      <TableCell>
        <Select value={r.priority} disabled={disabled} onValueChange={(v) => run(() => requirementsApi.patch(r.id, { priority: v as Priority }))}>
          <SelectTrigger className="h-8 text-xs" aria-label={`${r.display_id} priority`}><SelectValue /></SelectTrigger>
          <SelectContent>{PRIORITIES.map((p) => <SelectItem key={p} value={p}>{PRIORITY_LABELS[p]}</SelectItem>)}</SelectContent>
        </Select>
        {r.priority_basis && <p className="mt-1 text-[11px] text-muted-foreground">Basis: “{r.priority_basis}”</p>}
      </TableCell>
      <TableCell><SourceCell r={r} /></TableCell>
      <TableCell>
        {r.is_removed ? (
          <span className="text-xs">Removed</span>
        ) : r.needs_clarification && !r.clarification_waived ? (
          <div className="space-y-1">
            <span className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800"><AlertTriangle className="size-3.5" aria-hidden /> Needs clarification</span>
            {r.clarifying_question && <p className="text-xs text-amber-900">{r.clarifying_question}</p>}
            <Button size="sm" variant="link" className="h-auto p-0 text-xs" disabled={locked} onClick={() => run(() => requirementsApi.waive(r.id))}>Keep as written</Button>
          </div>
        ) : r.buyer_confirmed ? (
          <span className="inline-flex items-center gap-1 rounded-md border border-green-200 bg-green-50 px-2 py-0.5 text-xs font-medium text-green-800"><Check className="size-3.5" aria-hidden /> Confirmed</span>
        ) : (
          <span className="inline-flex items-center rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-700">Unconfirmed{r.clarification_waived ? " (kept as written)" : ""}</span>
        )}
      </TableCell>
      <TableCell>
        <div className="flex flex-wrap gap-1">
          {r.is_removed ? (
            <Button size="icon" variant="ghost" aria-label={`Restore ${r.display_id}`} disabled={locked} onClick={() => run(() => requirementsApi.restore(r.id))}><RotateCcw aria-hidden /></Button>
          ) : (
            <>
              {!r.buyer_confirmed && (!r.needs_clarification || r.clarification_waived) && (
                <Button size="icon" variant="ghost" aria-label={`Confirm ${r.display_id}`} disabled={locked} onClick={() => run(() => requirementsApi.confirm(r.id))}><Check aria-hidden /></Button>
              )}
              <Button size="icon" variant="ghost" aria-label={`Edit ${r.display_id}`} disabled={locked} onClick={() => setEditing(true)}><PenLine aria-hidden /></Button>
              <ConfirmDialog
                trigger={<Button size="icon" variant="ghost" aria-label={`Remove ${r.display_id}`} disabled={locked}><Trash2 aria-hidden /></Button>}
                title={`Remove ${r.display_id}?`}
                description="It is excluded from future assessments. You can restore it from 'Show removed'."
                confirmLabel="Remove"
                destructive
                onConfirm={() => run(() => requirementsApi.remove(r.id))}
              />
            </>
          )}
          <HistorySheet r={r} />
        </div>
      </TableCell>
    </TableRow>
  );
}

function SourceCell({ r }: { r: Requirement }) {
  const ref = r.source_reference;
  const Icon = r.source_type === "PDF" ? FileText : r.source_type === "CHAT" ? MessageSquare : r.source_type === "FORM" ? ListChecks : Keyboard;
  const tip =
    r.source_type === "PDF"
      ? `${ref.filename ?? "PDF"}${ref.page ? `, page ${ref.page}` : ""}: “${ref.quote ?? r.original_text}”`
      : r.source_type === "FORM"
        ? `Guided form: ${ref.field_label ?? ref.field_key}`
        : r.source_type === "CHAT"
          ? `Chat: “${ref.quote ?? r.original_text}”`
          : "Added manually";
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex cursor-help items-center gap-1 rounded-md border bg-slate-50 px-1.5 py-0.5 text-xs" tabIndex={0}>
          <Icon className="size-3.5" aria-hidden />
          {r.source_type === "PDF" && ref.page ? `p.${ref.page}` : r.source_type.toLowerCase()}
          {r.source_type === "PDF" && ref.quote_verified === false && <AlertTriangle className="size-3.5 text-amber-600" aria-label="Source text not located in the document" />}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        {tip}
        {r.source_type === "PDF" && ref.quote_verified === false && <p className="mt-1 font-semibold text-amber-300">Source text not located in the document</p>}
      </TooltipContent>
    </Tooltip>
  );
}

function HistorySheet({ r }: { r: Requirement }) {
  const userKey = useUserKey();
  const [open, setOpen] = useState(false);
  const q = useQuery({ queryKey: ["req-history", userKey, r.id], queryFn: () => requirementsApi.history(r.id), enabled: open });
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button size="icon" variant="ghost" aria-label={`History of ${r.display_id}`}><History aria-hidden /></Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{r.display_id} history</SheetTitle>
          <SheetDescription>Every change is recorded. The original text never changes.</SheetDescription>
        </SheetHeader>
        <p className="rounded-md bg-slate-50 p-2 text-sm"><span className="text-xs font-semibold uppercase text-muted-foreground">Original</span><br />{r.original_text}</p>
        {q.isLoading && <LoadingRows rows={3} />}
        <ol className="space-y-2">
          {q.data?.map((v) => (
            <li key={v.revision_no} className="rounded-md border p-2 text-sm">
              <p className="font-medium">#{v.revision_no} {v.change_type.replaceAll("_", " ").toLowerCase()} <span className="text-xs font-normal text-muted-foreground">by {v.actor ?? "system"} via {v.origin.toLowerCase()} · {formatDateTime(v.created_at)}</span></p>
              <ul className="mt-1 space-y-0.5 text-xs">
                {Object.entries(v.changes).map(([k, c]) => (
                  <li key={k}><span className="font-mono">{k}</span>: {typeof c === "object" && c ? <><span className="text-slate-500 line-through">{String(c.before ?? "—")}</span> → {String(c.after)}</> : String(c)}</li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </SheetContent>
    </Sheet>
  );
}

function AddRow({ assessment, onAdded }: { assessment: Assessment; onAdded: () => void }) {
  const [text, setText] = useState("");
  const [category, setCategory] = useState<RequirementCategory>("OTHER");
  const [priority, setPriority] = useState<Priority>("NOT_SPECIFIED");
  const add = useMutation({
    mutationFn: () => assessmentsApi.addRequirement(assessment.id, { normalized_text: text.trim(), category, priority }),
    onSuccess: () => { setText(""); toast.success("Requirement added"); onAdded(); },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="grid gap-2 rounded-lg border bg-card p-3 md:grid-cols-[1fr_12rem_10rem_auto]">
      <Textarea rows={1} value={text} onChange={(e) => setText(e.target.value)} placeholder="Add a requirement in your own words…" aria-label="New requirement text" />
      <Select value={category} onValueChange={(v) => setCategory(v as RequirementCategory)}>
        <SelectTrigger aria-label="New requirement category"><SelectValue /></SelectTrigger>
        <SelectContent>{CATEGORIES.map((c) => <SelectItem key={c} value={c}>{CATEGORY_LABELS[c]}</SelectItem>)}</SelectContent>
      </Select>
      <Select value={priority} onValueChange={(v) => setPriority(v as Priority)}>
        <SelectTrigger aria-label="New requirement priority"><SelectValue /></SelectTrigger>
        <SelectContent>{PRIORITIES.map((p) => <SelectItem key={p} value={p}>{PRIORITY_LABELS[p]}</SelectItem>)}</SelectContent>
      </Select>
      <Button onClick={() => add.mutate()} disabled={text.trim().length < 5 || add.isPending}><Plus aria-hidden /> Add requirement</Button>
    </div>
  );
}
