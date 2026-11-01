import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useUserKey } from "@/hooks/useIdentity";
import { jobsApi } from "@/services/jobs";
import type { Job } from "@/types/api";

/** Polls GET /api/jobs/{id} every 1.5 s until the job succeeds or fails. */
export function useJob(jobId: string | null | undefined) {
  const userKey = useUserKey();
  const q = useQuery({
    queryKey: ["job", userKey, jobId],
    queryFn: () => jobsApi.get(jobId as string),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "SUCCEEDED" || s === "FAILED" ? false : 1500;
    },
  });
  const job = q.data;
  return {
    job,
    error: q.error,
    running: !!jobId && (!job || job.status === "QUEUED" || job.status === "RUNNING"),
    done: job?.status === "SUCCEEDED",
    failed: job?.status === "FAILED",
  };
}

// Job ids whose completion was already handled in this page session. Kept outside the component so a
// remount (e.g. switching back to the Requirements tab) does not replay the toast and tab switch.
const handledJobs = new Set<string>();

/** Calls onFinish exactly once per job id when the job reaches SUCCEEDED or FAILED. */
export function useJobFinished(job: Job | undefined, onFinish: (job: Job) => void) {
  const cb = useRef(onFinish);
  useEffect(() => {
    cb.current = onFinish;
  });
  useEffect(() => {
    if (job && (job.status === "SUCCEEDED" || job.status === "FAILED") && !handledJobs.has(job.id)) {
      handledJobs.add(job.id);
      cb.current(job);
    }
  }, [job]);
}
