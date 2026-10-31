import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, FileUp, ScanLine } from "lucide-react";
import { type DragEvent, useRef, useState } from "react";
import { toast } from "sonner";
import { JobProgress } from "@/components/shared/JobProgress";
import { ErrorState } from "@/components/shared/States";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useUserKey } from "@/hooks/useIdentity";
import { useJob, useJobFinished } from "@/hooks/useJob";
import { cn, formatDateTime } from "@/lib/utils";
import { assessmentsApi } from "@/services/assessments";
import type { Assessment } from "@/types/api";

const MAX_MB = 20;

export function UploadPdfPanel({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const docs = useQuery({ queryKey: ["documents", userKey, assessment.id], queryFn: () => assessmentsApi.documents(assessment.id) });
  const { job, running } = useJob(jobId);

  const upload = useMutation({
    mutationFn: (f: File) => assessmentsApi.upload(assessment.id, f),
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["documents", userKey, assessment.id] });
      if (d.extraction_status === "OK") toast.success(`${d.original_filename} uploaded (${d.page_count} pages)`);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const extract = useMutation({
    mutationFn: (docId: string) => assessmentsApi.extract(assessment.id, docId),
    onSuccess: (r) => setJobId(r.job_id),
    onError: (e: Error) => toast.error(e.message),
  });
  useJobFinished(job, (j) => {
    qc.invalidateQueries({ queryKey: ["requirements", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
    if (j.status === "SUCCEEDED") {
      const r = j.result as { created: number; duplicates_skipped: number; needs_clarification_count: number; truncated: boolean };
      toast.success(`${r.created} requirements extracted${r.duplicates_skipped ? `, ${r.duplicates_skipped} duplicates skipped` : ""}. Please review and confirm them below.`);
    } else toast.error(j.error_message ?? "Extraction failed");
  });

  const pick = (files: FileList | null) => {
    const f = files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) return toast.error("Only .pdf files are accepted.");
    if (f.size > MAX_MB * 1024 * 1024) return toast.error(`The file is larger than ${MAX_MB} MB.`);
    upload.mutate(f);
  };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    pick(e.dataTransfer.files);
  };
  const latest = docs.data?.[0];

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={cn("flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-6 text-center", drag ? "border-primary bg-accent" : "border-slate-300")}
      >
        <FileUp className="size-6 text-slate-500" aria-hidden />
        <p className="text-sm">Drag a requirements PDF here, or</p>
        <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()} disabled={upload.isPending}>
          {upload.isPending ? "Uploading…" : "Choose a PDF"}
        </Button>
        <input ref={inputRef} type="file" accept="application/pdf,.pdf" className="sr-only" aria-label="Upload a PDF" onChange={(e) => { pick(e.target.files); e.target.value = ""; }} />
        <p className="text-xs text-muted-foreground">Text-based PDFs up to {MAX_MB} MB. The file is treated as untrusted data and never executed.</p>
      </div>
      {latest?.extraction_status === "SCANNED" && (
        <Alert variant="warning">
          <ScanLine aria-hidden />
          <AlertTitle>Scanned document</AlertTitle>
          <AlertDescription>{latest.extraction_message}</AlertDescription>
        </Alert>
      )}
      {running && <JobProgress job={job} label="Extracting requirements" />}
      {docs.error && <ErrorState error={docs.error} onRetry={() => docs.refetch()} />}
      {!!docs.data?.length && (
        <ul className="divide-y rounded-lg border bg-card">
          {docs.data.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center gap-3 p-3 text-sm">
              <FileText className="size-4 text-slate-500" aria-hidden />
              <span className="min-w-0 flex-1 truncate font-medium">{d.original_filename}</span>
              <span className="text-xs text-muted-foreground">{d.page_count} pages · {formatDateTime(d.created_at)}</span>
              {d.extraction_status === "OK" ? (
                <Button size="sm" onClick={() => extract.mutate(d.id)} disabled={running || extract.isPending}>
                  Extract requirements
                </Button>
              ) : (
                <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-800">Not readable ({d.extraction_status.toLowerCase()})</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
