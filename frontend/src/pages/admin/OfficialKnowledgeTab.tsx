import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ExternalLink, RefreshCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { JobProgress } from "@/components/shared/JobProgress";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUserKey } from "@/hooks/useIdentity";
import { useJob, useJobFinished } from "@/hooks/useJob";
import { formatDateTime } from "@/lib/utils";
import { knowledgeApi } from "@/services/knowledge";
import type { OkfFileRow } from "@/types/api";

const FILE_STATUS: Record<OkfFileRow["status"], { label: string; cls: string }> = {
  INDEXED: { label: "Indexed", cls: "bg-green-50 text-green-800 border-green-200" },
  SKIPPED_NOT_APPROVED: { label: "Draft — not indexed", cls: "bg-slate-100 text-slate-700 border-slate-200" },
  REMOVED: { label: "Removed", cls: "bg-slate-100 text-slate-500 border-slate-200" },
  ERROR: { label: "Error", cls: "bg-red-50 text-red-800 border-red-200" },
};

export function OfficialKnowledgeTab() {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const status = useQuery({ queryKey: ["knowledge-status", userKey], queryFn: knowledgeApi.status });
  const [jobId, setJobId] = useState<string | null>(null);
  const activeJob = jobId ?? status.data?.running_job_id ?? null;
  const { job, running } = useJob(activeJob);

  const reindex = useMutation({
    mutationFn: knowledgeApi.reindex,
    onSuccess: (r) => setJobId(r.job_id),
    onError: (e: Error) => toast.error(e.message),
  });

  useJobFinished(job, (j) => {
    qc.invalidateQueries({ queryKey: ["knowledge-status", userKey] });
    if (j.status === "SUCCEEDED") toast.success("Re-ingestion finished");
    else toast.error(j.error_message ?? "Re-ingestion failed");
  });

  if (status.isLoading) return <LoadingRows rows={6} />;
  if (status.error) return <ErrorState error={status.error} onRetry={() => status.refetch()} />;
  const s = status.data!;
  const run = s.last_run;
  const indexed = s.files.filter((f) => f.status === "INDEXED");

  return (
    <div className="space-y-4">
      {s.reindex_required && (
        <Alert variant="destructive">
          <AlertTriangle aria-hidden />
          <AlertTitle>Reindex required</AlertTitle>
          <AlertDescription>
            <ul className="list-disc pl-4">
              {s.reindex_problems.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
            Knowledge retrieval is disabled until the index is rebuilt with the configured embedding model.
          </AlertDescription>
        </Alert>
      )}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Official files indexed" value={indexed.length} />
        <Stat label="Official chunks in Qdrant" value={s.points.official ?? "unavailable"} />
        <Stat label="Expert-answer points in Qdrant" value={s.points.resolved ?? "unavailable"} />
        <Stat label="Knowledge epoch" value={s.epoch} />
      </div>
      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-base">Last ingestion run</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Format: {s.spec.format} v{s.spec.version} ·{" "}
              <a className="underline" href={s.spec.source} target="_blank" rel="noopener noreferrer">
                specification
              </a>
            </p>
          </div>
          <Button onClick={() => reindex.mutate()} disabled={running || reindex.isPending}>
            <RefreshCw className={running ? "animate-spin" : ""} aria-hidden /> Re-ingest
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {running && <JobProgress job={job} label="Re-ingesting the OKF bundle" />}
          {run ? (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-4">
              <Item k="Status" v={run.status} />
              <Item k="Finished" v={formatDateTime(run.finished_at)} />
              <Item k="Mode" v={run.mode} />
              <Item k="Triggered by" v={run.triggered_by} />
              <Item k="Files scanned" v={run.files_scanned} />
              <Item k="Added / updated" v={`${run.added} / ${run.updated}`} />
              <Item k="Unchanged" v={run.unchanged} />
              <Item k="Removed / skipped" v={`${run.removed} / ${run.skipped}`} />
              <Item k="Chunks upserted" v={run.chunks_upserted} />
              <Item k="Chunks deleted" v={run.chunks_deleted} />
              <Item k="Errors" v={run.errors.length} />
              <Item k="Embedding model" v={run.embedding_model} />
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">No ingestion has run yet. Run make ingest or click Re-ingest.</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Knowledge files ({s.files.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Chunks</TableHead>
                <TableHead>Hash</TableHead>
                <TableHead>Last verified</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {s.files.map((f) => (
                <TableRow key={f.path}>
                  <TableCell className="max-w-[22rem]">
                    <p className="truncate font-medium">{f.title ?? f.path}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {f.knowledge_id} ·{" "}
                      {f.source_url && (
                        <a href={f.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 underline">
                          source <ExternalLink className="size-3" aria-hidden />
                        </a>
                      )}
                    </p>
                    {f.error && <p className="text-xs text-red-700">{f.error}</p>}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={FILE_STATUS[f.status].cls}>
                      {FILE_STATUS[f.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{f.chunk_count}</TableCell>
                  <TableCell className="font-mono text-xs">{f.content_hash}</TableCell>
                  <TableCell className="whitespace-nowrap text-xs">{f.last_verified_at}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function Item({ k, v }: { k: string; v: string | number }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-muted-foreground">{k}</dt>
      <dd className="truncate font-medium">{v}</dd>
    </div>
  );
}
