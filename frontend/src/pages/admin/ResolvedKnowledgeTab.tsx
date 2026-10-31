import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { Markdown } from "@/components/shared/Markdown";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { adminApi } from "@/services/admin";
import type { ResolvedRecord } from "@/types/api";

const VALIDITY = {
  ACTIVE: "bg-green-50 text-green-800 border-green-200",
  SUPERSEDED: "bg-slate-100 text-slate-700 border-slate-200",
  REVOKED: "bg-red-50 text-red-800 border-red-200",
};

export function ResolvedKnowledgeTab() {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["resolved", userKey], queryFn: adminApi.resolved });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["resolved", userKey] });
    qc.invalidateQueries({ queryKey: ["knowledge-status", userKey] });
  };
  if (q.isLoading) return <LoadingRows rows={4} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data?.length) return <EmptyState title="No expert answers yet" description="Approved ticket answers appear here once published." />;
  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Question and answer</TableHead>
            <TableHead>Validity</TableHead>
            <TableHead className="text-right">Version</TableHead>
            <TableHead>Approved</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {q.data.map((r) => (
            <TableRow key={r.id} className="align-top">
              <TableCell className="max-w-xl">
                <p className="font-medium">{r.question_normalised}</p>
                <div className="mt-1 line-clamp-3 text-xs text-muted-foreground">{r.answer}</div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {r.ticket_display_id ?? "—"} · author {r.author}
                  {r.index_status !== "INDEXED" && ` · index ${r.index_status.toLowerCase()}`}
                  {r.status_reason && ` · ${r.status_reason}`}
                </p>
              </TableCell>
              <TableCell>
                <span className={cn("rounded-md border px-2 py-0.5 text-xs font-medium", VALIDITY[r.validity])}>{r.validity.toLowerCase()}</span>
              </TableCell>
              <TableCell className="text-right tabular-nums">v{r.version}</TableCell>
              <TableCell className="whitespace-nowrap text-xs">
                {r.approver}
                <br />
                {formatDateTime(r.approved_at)}
              </TableCell>
              <TableCell>
                {r.validity === "ACTIVE" && (
                  <div className="flex flex-col gap-1">
                    <SupersedeDialog r={r} onDone={refresh} />
                    <ConfirmDialog
                      trigger={<Button size="sm" variant="outline" className="text-red-700">Revoke</Button>}
                      title="Revoke this expert answer?"
                      description="It will immediately stop being retrieved. The record is kept for audit."
                      confirmLabel="Revoke"
                      destructive
                      reasonLabel="Reason (required)"
                      onConfirm={async (reason) => {
                        await adminApi.revoke(r.id, reason);
                        toast.success("Answer revoked");
                        refresh();
                      }}
                    />
                  </div>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function SupersedeDialog({ r, onDone }: { r: ResolvedRecord; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState(r.answer);
  const [ok, setOk] = useState(false);
  const m = useMutation({
    mutationFn: () => adminApi.supersede(r.id, { answer, privacy_confirmed: ok }),
    onSuccess: (n) => {
      toast.success(`Published version ${n.version}`);
      setOpen(false);
      onDone();
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          Supersede
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Publish a new version</DialogTitle>
          <DialogDescription>{r.question_normalised}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="sup-ans">Answer (Markdown)</Label>
            <Textarea id="sup-ans" rows={8} value={answer} onChange={(e) => setAnswer(e.target.value)} />
            {answer.trim().length < 40 && <p className="text-xs text-red-700">At least 40 characters.</p>}
          </div>
          <div className="rounded-md border bg-slate-50 p-3 text-sm">
            <Markdown text={answer} />
          </div>
        </div>
        <div className="flex items-start gap-2">
          <Checkbox id="sup-priv" checked={ok} onCheckedChange={(c) => setOk(c === true)} />
          <Label htmlFor="sup-priv" className="leading-snug">
            This answer contains no buyer-private or customer-specific information
          </Label>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={() => m.mutate()} disabled={!ok || answer.trim().length < 40 || m.isPending}>
            Publish version {r.version + 1}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
