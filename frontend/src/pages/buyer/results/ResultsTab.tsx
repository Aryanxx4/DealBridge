import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BookOpenCheck, Info, Play, Search, ShieldAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { PriorityBadge } from "@/components/shared/Badges";
import { JobProgress } from "@/components/shared/JobProgress";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { STATUS_META, STATUS_ORDER, StatusBadge } from "@/components/shared/StatusBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { analysisApi } from "@/services/analysis";
import { type Assessment, type AssessmentResults, CATEGORY_LABELS, type FitStatus, PRIORITY_LABELS, type Priority, type RequirementCategory, type RequirementResult } from "@/types/api";
import { useRunAssessment } from "../requirements/RequirementsFooter";
import { RequirementDetailSheet } from "./RequirementDetailSheet";
import { ResultsActions } from "./resultsActions";

export function ResultsTab({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const [version, setVersion] = useState<number | undefined>(undefined);
  const versions = useQuery({ queryKey: ["versions", userKey, assessment.id], queryFn: () => analysisApi.versions(assessment.id), enabled: assessment.latest_version_no > 0 });
  const results = useQuery({ queryKey: ["results", userKey, assessment.id, version ?? "latest"], queryFn: () => analysisApi.results(assessment.id, version), enabled: assessment.latest_version_no > 0 });
  const pending = useQuery({ queryKey: ["pending", userKey, assessment.id], queryFn: () => analysisApi.pending(assessment.id), enabled: assessment.latest_version_no > 0 });
  const { run, job, running } = useRunAssessment(assessment);

  if (assessment.latest_version_no === 0) {
    return running ? (
      <JobProgress job={job} label="Running the assessment" />
    ) : (
      <EmptyState icon={<BookOpenCheck className="size-8" aria-hidden />} title="No results yet" description="Confirm your requirements on the Requirements tab, then run the assessment." />
    );
  }
  if (results.isLoading) return <LoadingRows rows={6} />;
  if (results.error) return <ErrorState error={results.error} onRetry={() => results.refetch()} />;
  const r = results.data!;
  const isLatest = r.version.version_no === assessment.latest_version_no;
  const pendingCount = pending.data?.changes.length ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Select value={String(r.version.version_no)} onValueChange={(v) => setVersion(Number(v) === assessment.latest_version_no ? undefined : Number(v))}>
          <SelectTrigger className="w-72" aria-label="Assessment version"><SelectValue /></SelectTrigger>
          <SelectContent>
            {(versions.data ?? []).map((v) => (
              <SelectItem key={v.version_no} value={String(v.version_no)}>Version {v.version_no}, {formatDateTime(v.analyzed_at)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="ml-auto flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => run.mutate()} disabled={running || run.isPending}><Play aria-hidden /> Re-run assessment</Button>
          {ResultsActions.map((A, i) => <A key={i} assessment={assessment} versionNo={r.version.version_no} />)}
        </div>
      </div>
      {running && <JobProgress job={job} label="Running the assessment" />}
      {!isLatest && <Alert variant="info"><Info aria-hidden /><AlertDescription>You are viewing an earlier version ({r.version.version_no}). It is kept unchanged for comparison.</AlertDescription></Alert>}
      {isLatest && assessment.status === "STALE" && (
        <Alert variant="warning"><AlertTriangle aria-hidden /><AlertDescription>These results are out of date: {pendingCount || "some"} change(s) since the last assessment. Re-run the assessment to update them.</AlertDescription></Alert>
      )}
      {isLatest && assessment.status !== "STALE" && pendingCount > 0 && (
        <Alert variant="warning"><AlertTriangle aria-hidden /><AlertDescription>{pendingCount} change(s) since the last assessment.</AlertDescription></Alert>
      )}
      {r.knowledge_updated && <Alert variant="info"><Info aria-hidden /><AlertDescription>Product knowledge has been updated since this assessment. Re-run it to include the new knowledge.</AlertDescription></Alert>}
      <SummaryCard r={r} />
      <RequirementList items={r.requirements} assessmentId={assessment.id} />
    </div>
  );
}

function SummaryCard({ r }: { r: AssessmentResults }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Summary — version {r.version.version_no}</CardTitle>
        <p className="text-xs text-muted-foreground">Analysed {formatDateTime(r.version.analyzed_at)} · preliminary, evidence-based assessment (not a guarantee)</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed">{r.summary.executive_summary}</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {STATUS_ORDER.map((s) => {
            const m = STATUS_META[s];
            return (
              <div key={s} className={cn("rounded-lg border p-3", m.cls)}>
                <div className="flex items-center gap-1 text-xs font-medium"><m.Icon className="size-3.5" aria-hidden />{m.label}</div>
                <p className="mt-1 text-2xl font-semibold tabular-nums">{r.summary.status_counts[s] ?? 0}</p>
              </div>
            );
          })}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="flex items-center gap-1 text-sm font-semibold"><ShieldAlert className="size-4 text-red-700" aria-hidden /> Potential blockers</p>
            {r.summary.blockers.length ? (
              <p className="mt-1 text-sm">{r.summary.blockers.join(", ")} <span className="text-xs text-muted-foreground">(critical or high priority and not established as supported)</span></p>
            ) : <p className="mt-1 text-sm text-muted-foreground">None identified.</p>}
          </div>
          <div>
            <p className="text-sm font-semibold">Recommended next steps</p>
            <ol className="mt-1 list-decimal space-y-0.5 pl-5 text-sm">{r.summary.next_steps.map((s) => <li key={s}>{s}</li>)}</ol>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RequirementList({ items, assessmentId }: { items: RequirementResult[]; assessmentId: string }) {
  const [status, setStatus] = useState<"all" | FitStatus>("all");
  const [category, setCategory] = useState<"all" | RequirementCategory>("all");
  const [priority, setPriority] = useState<"all" | Priority>("all");
  const [blockers, setBlockers] = useState(false);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<RequirementResult | null>(null);
  const shown = useMemo(
    () =>
      items.filter(
        (i) =>
          (status === "all" || i.status === status) &&
          (category === "all" || i.category === category) &&
          (priority === "all" || i.priority === priority) &&
          (!blockers || i.is_blocker) &&
          (!search || `${i.display_id} ${i.text}`.toLowerCase().includes(search.toLowerCase())),
      ),
    [items, status, category, priority, blockers, search],
  );
  return (
    <Card>
      <CardHeader className="space-y-3">
        <CardTitle className="text-base">Requirements ({items.length})</CardTitle>
        <div className="flex flex-wrap items-end gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 size-4 text-muted-foreground" aria-hidden />
            <Input className="w-56 pl-8" placeholder="Search requirements" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search requirements" />
          </div>
          <Select value={status} onValueChange={(v) => setStatus(v as typeof status)}>
            <SelectTrigger className="w-44" aria-label="Filter by status"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">All statuses</SelectItem>{STATUS_ORDER.map((s) => <SelectItem key={s} value={s}>{STATUS_META[s].label}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={category} onValueChange={(v) => setCategory(v as typeof category)}>
            <SelectTrigger className="w-52" aria-label="Filter by category"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">All categories</SelectItem>{(Object.keys(CATEGORY_LABELS) as RequirementCategory[]).map((c) => <SelectItem key={c} value={c}>{CATEGORY_LABELS[c]}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={priority} onValueChange={(v) => setPriority(v as typeof priority)}>
            <SelectTrigger className="w-40" aria-label="Filter by priority"><SelectValue /></SelectTrigger>
            <SelectContent><SelectItem value="all">All priorities</SelectItem>{(Object.keys(PRIORITY_LABELS) as Priority[]).map((p) => <SelectItem key={p} value={p}>{PRIORITY_LABELS[p]}</SelectItem>)}</SelectContent>
          </Select>
          <div className="flex items-center gap-2 pb-2">
            <Checkbox id="blockers-only" checked={blockers} onCheckedChange={(c) => setBlockers(c === true)} />
            <Label htmlFor="blockers-only" className="text-sm font-normal">Blockers only</Label>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {shown.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">No requirements match these filters.</p>
        ) : (
          <ul className="divide-y">
            {shown.map((i) => (
              <li key={i.requirement_id}>
                <button type="button" className="flex w-full flex-wrap items-center gap-3 px-5 py-3 text-left hover:bg-slate-50" onClick={() => setOpen(i)}>
                  <span className="font-mono text-xs text-muted-foreground">{i.display_id}</span>
                  <span className="min-w-0 flex-1 text-sm">{i.text}</span>
                  {i.is_blocker && <span className="rounded-md border border-red-200 bg-red-50 px-1.5 text-xs text-red-800">Blocker</span>}
                  {i.answer_available && <span className="rounded-md border border-violet-200 bg-violet-50 px-1.5 text-xs text-violet-800">Expert answer available</span>}
                  <PriorityBadge priority={i.priority} />
                  <StatusBadge status={i.status} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
      <RequirementDetailSheet item={open} assessmentId={assessmentId} onClose={() => setOpen(null)} />
    </Card>
  );
}
