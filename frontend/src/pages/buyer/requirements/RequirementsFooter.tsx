import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { JobProgress } from "@/components/shared/JobProgress";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useUserKey } from "@/hooks/useIdentity";
import { useJob, useJobFinished } from "@/hooks/useJob";
import { analysisApi } from "@/services/analysis";
import { ApiError } from "@/services/api";
import type { Assessment } from "@/types/api";
import { useRequirements } from "./ReviewTable";

export function useRunAssessment(assessment: Assessment) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [, setParams] = useSearchParams();
  const run = useMutation({
    mutationFn: () => analysisApi.run(assessment.id),
    onSuccess: (r) => {
      qc.setQueryData(["analysis-job", userKey, assessment.id], r.job_id);
      qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : String(e)),
  });
  const jobId = (qc.getQueryData(["analysis-job", userKey, assessment.id]) as string | undefined) ?? run.data?.job_id ?? null;
  const { job, running } = useJob(jobId);
  useJobFinished(job, (j) => {
    qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["results", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["versions", userKey, assessment.id] });
    qc.invalidateQueries({ queryKey: ["pending", userKey, assessment.id] });
    if (j.status === "SUCCEEDED") {
      toast.success(`Assessment complete: version ${(j.result as { version_no: number }).version_no}`);
      setParams({ tab: "results" });
    } else toast.error(`Assessment failed: ${j.error_message ?? j.error_code} No new version was created.`);
  });
  return { run, job, running: running || assessment.status === "ANALYZING" };
}

export function RequirementsFooter({ assessment }: { assessment: Assessment }) {
  const q = useRequirements(assessment.id, false);
  const rows = q.data ?? [];
  const confirmed = rows.filter((r) => r.buyer_confirmed).length;
  const clarify = rows.filter((r) => r.needs_clarification && !r.clarification_waived).length;
  const excluded = rows.length - confirmed;
  const { run, job, running } = useRunAssessment(assessment);
  return (
    <div className="fixed inset-x-0 bottom-0 z-30 border-t bg-card/95 backdrop-blur">
      <div className="mx-auto max-w-7xl space-y-2 px-4 py-3">
        {running && <JobProgress job={job} label="Running the assessment" />}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
          <span><strong className="tabular-nums">{rows.length}</strong> active</span>
          <span><strong className="tabular-nums">{confirmed}</strong> confirmed</span>
          <span><strong className="tabular-nums">{excluded}</strong> unconfirmed</span>
          {clarify > 0 && <span className="text-amber-800"><strong className="tabular-nums">{clarify}</strong> need clarification</span>}
          <div className="ml-auto flex items-center gap-3">
            {confirmed > 0 && excluded > 0 && <span className="text-xs text-amber-800">{excluded} unconfirmed requirement(s) will be excluded.</span>}
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={confirmed === 0 ? 0 : -1}>
                  <Button onClick={() => run.mutate()} disabled={confirmed === 0 || running || run.isPending}>
                    <Play aria-hidden /> {assessment.latest_version_no ? "Re-run assessment" : "Run assessment"}
                  </Button>
                </span>
              </TooltipTrigger>
              {confirmed === 0 && <TooltipContent>Confirm at least one requirement first. Only confirmed requirements are assessed.</TooltipContent>}
            </Tooltip>
          </div>
        </div>
      </div>
    </div>
  );
}
