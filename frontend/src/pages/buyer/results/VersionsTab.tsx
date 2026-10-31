import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { STATUS_META, STATUS_ORDER, StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { analysisApi } from "@/services/analysis";
import { type Assessment, PRIORITY_LABELS, type VersionChange } from "@/types/api";

const CHANGE_LABEL: Record<VersionChange["change"], { label: string; cls: string }> = {
  ADDED: { label: "Added", cls: "bg-green-50 text-green-800 border-green-200" },
  REMOVED: { label: "Removed", cls: "bg-red-50 text-red-800 border-red-200" },
  TEXT_CHANGED: { label: "Text changed", cls: "bg-blue-50 text-blue-800 border-blue-200" },
  PRIORITY_CHANGED: { label: "Priority changed", cls: "bg-amber-50 text-amber-800 border-amber-200" },
  STATUS_CHANGED: { label: "Status changed", cls: "bg-violet-50 text-violet-800 border-violet-200" },
  UNCHANGED: { label: "Unchanged", cls: "bg-white text-slate-500 border-slate-200" },
};

export function VersionsTab({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const versions = useQuery({ queryKey: ["versions", userKey, assessment.id], queryFn: () => analysisApi.versions(assessment.id), enabled: assessment.latest_version_no > 0 });
  const [from, setFrom] = useState<string>("");
  const [to, setTo] = useState<string>("");
  const [changedOnly, setChangedOnly] = useState(true);
  const ready = from && to && from !== to;
  const cmp = useQuery({ queryKey: ["compare", userKey, assessment.id, from, to], queryFn: () => analysisApi.compare(assessment.id, Number(from), Number(to)), enabled: !!ready });
  if (assessment.latest_version_no === 0) return <EmptyState title="No versions yet" description="Each assessment run creates a new version; earlier versions stay unchanged." />;
  if (versions.isLoading) return <LoadingRows rows={3} />;
  if (versions.error) return <ErrorState error={versions.error} onRetry={() => versions.refetch()} />;
  const rows = versions.data ?? [];
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-base">Versions</CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Version</TableHead>
                <TableHead>Analysed</TableHead>
                <TableHead>Requirements</TableHead>
                <TableHead>Status counts</TableHead>
                <TableHead>Requirement-set revision</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((v) => (
                <TableRow key={v.version_no}>
                  <TableCell className="font-medium">Version {v.version_no}</TableCell>
                  <TableCell className="whitespace-nowrap text-xs">{formatDateTime(v.analyzed_at)}</TableCell>
                  <TableCell className="tabular-nums">{v.requirement_count}</TableCell>
                  <TableCell className="text-xs">{STATUS_ORDER.filter((s) => v.status_counts[s]).map((s) => `${STATUS_META[s].label}: ${v.status_counts[s]}`).join(" · ")}</TableCell>
                  <TableCell className="tabular-nums">{v.requirement_set_revision}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">Compare two versions</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {rows.length < 2 ? (
            <p className="text-sm text-muted-foreground">Run the assessment again after changing requirements to compare versions.</p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <VersionPick value={from} onChange={setFrom} rows={rows.map((r) => r.version_no)} label="From version" />
              <ArrowRight className="size-4 text-muted-foreground" aria-hidden />
              <VersionPick value={to} onChange={setTo} rows={rows.map((r) => r.version_no)} label="To version" />
              {rows.length >= 2 && !ready && (
                <Button variant="outline" size="sm" onClick={() => { setFrom(String(rows[1].version_no)); setTo(String(rows[0].version_no)); }}>Compare the latest two</Button>
              )}
            </div>
          )}
          {cmp.data && (
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={changedOnly} onChange={(e) => setChangedOnly(e.target.checked)} />
              Show changed requirements only ({cmp.data.changes.filter((c) => c.change !== "UNCHANGED").length} of {cmp.data.changes.length})
            </label>
          )}
          {cmp.error && <ErrorState error={cmp.error} onRetry={() => cmp.refetch()} />}
          {cmp.data && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Requirement</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cmp.data.changes.filter((c) => !changedOnly || c.change !== "UNCHANGED").map((c) => (
                  <TableRow key={c.requirement_id} className={cn(c.change !== "UNCHANGED" && "bg-amber-50/30")}>
                    <TableCell className="font-mono text-xs">{c.display_id}</TableCell>
                    <TableCell><span className={cn("rounded-md border px-2 py-0.5 text-xs font-medium", CHANGE_LABEL[c.change].cls)}>{CHANGE_LABEL[c.change].label}</span></TableCell>
                    <TableCell className="max-w-md text-sm">
                      {c.change === "TEXT_CHANGED" ? <><p className="text-slate-500 line-through">{c.previous_text}</p><p>{c.new_text}</p></> : (c.new_text ?? c.previous_text)}
                    </TableCell>
                    <TableCell className="text-xs">{c.previous_priority && c.new_priority && c.previous_priority !== c.new_priority ? `${PRIORITY_LABELS[c.previous_priority]} → ${PRIORITY_LABELS[c.new_priority]}` : PRIORITY_LABELS[(c.new_priority ?? c.previous_priority)!]}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap items-center gap-1">
                        {c.previous_status && <StatusBadge status={c.previous_status} />}
                        {c.previous_status && c.new_status && c.previous_status !== c.new_status && <ArrowRight className="size-3" aria-hidden />}
                        {c.new_status && c.new_status !== c.previous_status && <StatusBadge status={c.new_status} />}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function VersionPick({ value, onChange, rows, label }: { value: string; onChange: (v: string) => void; rows: number[]; label: string }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-40" aria-label={label}><SelectValue placeholder={label} /></SelectTrigger>
      <SelectContent>{rows.map((n) => <SelectItem key={n} value={String(n)}>Version {n}</SelectItem>)}</SelectContent>
    </Select>
  );
}
