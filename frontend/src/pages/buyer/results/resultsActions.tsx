import { Download } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { sharingApi } from "@/services/sharing";
import type { Assessment } from "@/types/api";
import { ShareDialog } from "../sharing/ShareDialog";

function DownloadReport({ assessment, versionNo }: { assessment: Assessment; versionNo: number }) {
  const [busy, setBusy] = useState(false);
  return (
    <Button
      variant="outline"
      disabled={busy}
      onClick={async () => {
        setBusy(true);
        try {
          await sharingApi.report(assessment.id, versionNo);
        } catch (e) {
          toast.error(e instanceof Error ? e.message : "Download failed");
        } finally {
          setBusy(false);
        }
      }}
    >
      <Download aria-hidden /> {busy ? "Preparing…" : "Download PDF report"}
    </Button>
  );
}

function Share({ assessment, versionNo }: { assessment: Assessment; versionNo: number }) {
  return <ShareDialog assessment={assessment} versionNo={versionNo} />;
}

/** Page-level actions on the results tab. */
export const ResultsActions = [DownloadReport, Share];
