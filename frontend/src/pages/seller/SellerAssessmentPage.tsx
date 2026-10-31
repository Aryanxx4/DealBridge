import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Download } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { RequireRole } from "@/components/layout/RequireRole";
import { PriorityBadge } from "@/components/shared/Badges";
import { FollowUpStatusBadge, FollowUpThread } from "@/components/shared/FollowUpThread";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { STATUS_META, STATUS_ORDER, StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { sharingApi } from "@/services/sharing";
import type { FitStatus, RequirementResult } from "@/types/api";
import { ASSERTION_LABELS, RequirementDetailSheet } from "../buyer/results/RequirementDetailSheet";

export function SellerAssessmentPage() {
  return (
    <RequireRole roles={["SELLER"]}>
      <Inner />
    </RequireRole>
  );
}

function Inner() {
  const { id = "" } = useParams();
  const userKey = useUserKey();
  const [version, setVersion] = useState<number | undefined>();
  const [status, setStatus] = useState<"all" | FitStatus>("all");
  const [open, setOpen] = useState<RequirementResult | null>(null);
  const [thread, setThread] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["seller-assessment", userKey, id, version ?? "latest"], queryFn: () => sharingApi.sellerAssessment(id, version) });
  const fus = useQuery({ queryKey: ["follow-ups", userKey, id], queryFn: () => sharingApi.followUps(id) });
  const rows = useMemo(() => (q.data?.requirements ?? []).filter((r) => status === "all" || r.status === status), [q.data, status]);
  if (q.isLoading) return <LoadingRows rows={5} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const d = q.data!;
  const current = open ? d.requirements.find((r) => r.requirement_id === open.requirement_id) ?? open : null;
  return (
    <div className="space-y-4">
      <Link to="/seller" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" aria-hidden /> Shared assessments</Link>
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <p className="text-sm text-muted-foreground">{d.assessment.buyer_org} · shared by {d.assessment.buyer_name}</p>
          <h1 className="text-2xl font-semibold">{d.assessment.title}</h1>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Select value={String(d.version.version_no)} onValueChange={(v) => setVersion(Number(v))}>
            <SelectTrigger className="w-44" aria-label="Shared version"><SelectValue /></SelectTrigger>
            <SelectContent>{d.shared_versions.map((n) => <SelectItem key={n} value={String(n)}>Version {n}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" onClick={() => sharingApi.report(id, d.version.version_no).catch((e: Error) => toast.error(e.message))}><Download aria-hidden /> Download report</Button>
          <Button variant="outline" onClick={() => sharingApi.excel(id, d.version.version_no).catch((e: Error) => toast.error(e.message))}>Excel</Button>
        </div>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">Buyer context</CardTitle></CardHeader>
        <CardContent className="grid gap-2 text-sm sm:grid-cols-3">
          <p><span className="text-muted-foreground">Organisation:</span> {d.assessment.context.organisation_name ?? "—"}</p>
          <p><span className="text-muted-foreground">Industry:</span> {d.assessment.context.industry ?? "—"}</p>
          <p><span className="text-muted-foreground">Use case:</span> {d.assessment.context.use_case ?? "—"}</p>
          <p className="text-xs text-muted-foreground sm:col-span-3">Version {d.version.version_no} analysed {formatDateTime(d.version.analyzed_at)}. {d.summary.executive_summary}</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {STATUS_ORDER.map((s) => (
          <button key={s} type="button" onClick={() => setStatus(status === s ? "all" : s)} className={cn("rounded-lg border p-3 text-left", STATUS_META[s].cls, status === s && "ring-2 ring-primary")} aria-pressed={status === s}>
            <span className="flex items-center gap-1 text-xs font-medium">{STATUS_META[s].label}</span>
            <span className="text-2xl font-semibold tabular-nums">{d.summary.status_counts[s] ?? 0}</span>
          </button>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">Requirements (read-only)</CardTitle></CardHeader>
        <CardContent className="p-0">
          <ul className="divide-y">
            {rows.map((r) => (
              <li key={r.requirement_id}>
                <button type="button" className="flex w-full flex-wrap items-center gap-3 px-5 py-3 text-left hover:bg-slate-50" onClick={() => setOpen(r)}>
                  <span className="font-mono text-xs text-muted-foreground">{r.display_id}</span>
                  <span className="min-w-0 flex-1 text-sm">{r.text}</span>
                  {r.seller_responses.length > 0 && <span className="rounded-md border border-teal-200 bg-teal-50 px-1.5 text-xs text-teal-800">Responded</span>}
                  <PriorityBadge priority={r.priority} />
                  <StatusBadge status={r.status} />
                </button>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">Follow-ups</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {fus.data?.length === 0 && <p className="text-sm text-muted-foreground">No follow-up requests for this assessment.</p>}
          {fus.data?.map((f) => (
            <div key={f.id} className="rounded-lg border">
              <button type="button" className="flex w-full flex-wrap items-center gap-2 p-3 text-left" onClick={() => setThread(thread === f.id ? null : f.id)} aria-expanded={thread === f.id}>
                <span className="font-medium">{f.subject}</span><FollowUpStatusBadge status={f.status} />
              </button>
              {thread === f.id && <div className="border-t p-3"><FollowUpThread id={f.id} /></div>}
            </div>
          ))}
        </CardContent>
      </Card>
      <RequirementDetailSheet item={current} assessmentId={id} onClose={() => setOpen(null)} hideAsk sellerSlot={current && <ResponseForm requirementId={current.requirement_id} versionNo={d.version.version_no} assessmentId={id} />} />
    </div>
  );
}

function ResponseForm({ requirementId, versionNo, assessmentId }: { requirementId: string; versionNo: number; assessmentId: string }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [body, setBody] = useState("");
  const [assertion, setAssertion] = useState("NONE");
  const [file, setFile] = useState<File | null>(null);
  const m = useMutation({
    mutationFn: async () => {
      const r = (await sharingApi.sellerResponse(requirementId, { version_no: versionNo, body: body.trim(), assertion })) as { id: string };
      if (file) {
        const doc = await sharingApi.uploadSellerDocument(file);
        await sharingApi.attachToResponse(r.id, [doc.id]);
      }
      return r;
    },
    onSuccess: () => { toast.success("Response added"); setBody(""); setFile(null); qc.invalidateQueries({ queryKey: ["seller-assessment", userKey, assessmentId] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <div className="space-y-2 rounded-md border p-3">
      <Label htmlFor="seller-resp">Add a response</Label>
      <Select value={assertion} onValueChange={setAssertion}>
        <SelectTrigger aria-label="Response type"><SelectValue /></SelectTrigger>
        <SelectContent>{Object.entries(ASSERTION_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v}</SelectItem>)}</SelectContent>
      </Select>
      <Textarea id="seller-resp" rows={3} maxLength={4000} value={body} onChange={(e) => setBody(e.target.value)} />
      <label className="block text-xs">
        Attach a document (optional; PDF, .md or .txt — shown as seller-provided, never official knowledge)
        <input type="file" accept=".pdf,.md,.txt" className="mt-1 block text-xs" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      <p className="text-xs text-muted-foreground">Your response is attributed to you and does not change the system assessment.</p>
      <Button size="sm" onClick={() => m.mutate()} disabled={!body.trim() || m.isPending}>Submit response</Button>
    </div>
  );
}
