import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { RequireRole } from "@/components/layout/RequireRole";
import { FollowUpStatusBadge } from "@/components/shared/FollowUpThread";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { STATUS_META, STATUS_ORDER } from "@/components/shared/StatusBadge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUserKey } from "@/hooks/useIdentity";
import { formatDateTime } from "@/lib/utils";
import { sharingApi } from "@/services/sharing";

export function SellerHomePage() {
  const [params, setParams] = useSearchParams();
  return (
    <RequireRole roles={["SELLER"]}>
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Seller workspace</h1>
          <p className="text-sm text-muted-foreground">Only assessments that buyers have explicitly shared with your organisation appear here. You can respond, but you cannot change a buyer's requirements.</p>
        </div>
        <Tabs value={params.get("tab") ?? "shared"} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
          <TabsList>
            <TabsTrigger value="shared">Shared assessments</TabsTrigger>
            <TabsTrigger value="followups">Follow-ups</TabsTrigger>
          </TabsList>
          <TabsContent value="shared"><SharedList /></TabsContent>
          <TabsContent value="followups"><FollowUpQueue /></TabsContent>
        </Tabs>
      </div>
    </RequireRole>
  );
}

function SharedList() {
  const userKey = useUserKey();
  const navigate = useNavigate();
  const q = useQuery({ queryKey: ["seller-assessments", userKey], queryFn: sharingApi.sellerAssessments });
  if (q.isLoading) return <LoadingRows rows={3} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data?.length) return <EmptyState title="Nothing shared yet" description="When a buyer shares an assessment with your organisation, it appears here." />;
  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Buyer</TableHead>
            <TableHead>Assessment</TableHead>
            <TableHead>Shared version</TableHead>
            <TableHead>Status counts</TableHead>
            <TableHead className="text-right">Open follow-ups</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {q.data.map((a) => (
            <TableRow key={a.id} className="cursor-pointer" onClick={() => navigate(`/seller/assessments/${a.id}`)}>
              <TableCell>{a.buyer_org}<p className="text-xs text-muted-foreground">{a.buyer_name}</p></TableCell>
              <TableCell><a className="font-medium text-primary hover:underline" href={`/seller/assessments/${a.id}`} onClick={(e) => { e.preventDefault(); navigate(`/seller/assessments/${a.id}`); }}>{a.title}</a></TableCell>
              <TableCell>Version {a.shared_version}<p className="text-xs text-muted-foreground">{formatDateTime(a.shared_at)}</p></TableCell>
              <TableCell className="text-xs">{STATUS_ORDER.filter((s) => a.status_counts[s]).map((s) => `${STATUS_META[s].label}: ${a.status_counts[s]}`).join(" · ")}</TableCell>
              <TableCell className="text-right tabular-nums">{a.open_follow_ups}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function FollowUpQueue() {
  const userKey = useUserKey();
  const navigate = useNavigate();
  const [status, setStatus] = useState("open");
  const filter = status === "open" ? "REQUESTED,IN_PROGRESS,RESPONDED" : status === "all" ? undefined : status;
  const q = useQuery({ queryKey: ["follow-ups", userKey, "seller", filter], queryFn: () => sharingApi.sellerFollowUps(filter) });
  return (
    <div className="space-y-3">
      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-48" aria-label="Filter follow-ups"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="open">Open</SelectItem><SelectItem value="REQUESTED">Requested</SelectItem><SelectItem value="IN_PROGRESS">In progress</SelectItem>
          <SelectItem value="RESPONDED">Responded</SelectItem><SelectItem value="CLOSED">Closed</SelectItem><SelectItem value="all">All</SelectItem>
        </SelectContent>
      </Select>
      {q.isLoading && <LoadingRows rows={3} />}
      {q.error && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data?.length === 0 && <EmptyState title="No follow-ups" description="Follow-up requests from buyers appear here." />}
      <ul className="space-y-2">
        {q.data?.map((f) => (
          <li key={f.id}>
            <button type="button" className="flex w-full flex-wrap items-center gap-2 rounded-lg border bg-card p-3 text-left hover:border-primary" onClick={() => navigate(`/seller/follow-ups/${f.id}`)}>
              <span className="font-medium">{f.subject}</span>
              <FollowUpStatusBadge status={f.status} />
              <span className="text-xs text-muted-foreground">{f.buyer_org} · {f.assessment_title}</span>
              <span className="ml-auto text-xs text-muted-foreground">updated {formatDateTime(f.updated_at)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
