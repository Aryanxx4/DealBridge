import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { RequireRole } from "@/components/layout/RequireRole";
import { AssessmentStatusBadge } from "@/components/shared/Badges";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { formatDateTime } from "@/lib/utils";
import { assessmentsApi } from "@/services/assessments";

export function BuyerDashboardPage() {
  return (
    <RequireRole roles={["BUYER"]}>
      <Inner />
    </RequireRole>
  );
}

function Inner() {
  const userKey = useUserKey();
  const navigate = useNavigate();
  const q = useQuery({ queryKey: ["assessments", userKey], queryFn: assessmentsApi.list });
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Assessments</h1>
          <p className="text-sm text-muted-foreground">Your private product evaluations. Nothing is shared with a seller unless you explicitly share it.</p>
        </div>
        <NewAssessmentDialog />
      </div>
      {q.isLoading && <LoadingRows rows={4} />}
      {q.error && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data?.length === 0 && (
        <EmptyState
          icon={<ClipboardList className="size-8" aria-hidden />}
          title="No assessments yet"
          description="Create an assessment, then add your requirements by uploading a PDF, chatting, or filling in the guided form."
          action={<NewAssessmentDialog />}
        />
      )}
      {!!q.data?.length && (
        <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Latest version</TableHead>
                <TableHead className="text-right">Requirements</TableHead>
                <TableHead>Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {q.data.map((a) => (
                <TableRow key={a.id} className="cursor-pointer" onClick={() => navigate(`/buyer/assessments/${a.id}`)}>
                  <TableCell>
                    <a href={`/buyer/assessments/${a.id}`} className="font-medium text-primary hover:underline" onClick={(e) => { e.preventDefault(); navigate(`/buyer/assessments/${a.id}`); }}>
                      {a.title}
                    </a>
                    {a.context.organisation_name && <p className="text-xs text-muted-foreground">{a.context.organisation_name}</p>}
                  </TableCell>
                  <TableCell><AssessmentStatusBadge status={a.status} /></TableCell>
                  <TableCell>{a.latest_version_no ? `Version ${a.latest_version_no}` : "Not run yet"}</TableCell>
                  <TableCell className="text-right tabular-nums">{a.requirement_count} <span className="text-xs text-muted-foreground">({a.confirmed_count} confirmed)</span></TableCell>
                  <TableCell className="whitespace-nowrap text-xs">{formatDateTime(a.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function NewAssessmentDialog() {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [org, setOrg] = useState("");
  const [industry, setIndustry] = useState("");
  const [useCase, setUseCase] = useState("");
  const valid = title.trim().length >= 3 && title.trim().length <= 120;
  const m = useMutation({
    mutationFn: () => assessmentsApi.create({ title: title.trim(), context: { organisation_name: org, industry, use_case: useCase } }),
    onSuccess: (a) => {
      qc.invalidateQueries({ queryKey: ["assessments", userKey] });
      toast.success("Assessment created");
      setOpen(false);
      navigate(`/buyer/assessments/${a.id}`);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus aria-hidden /> New assessment
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New assessment</DialogTitle>
          <DialogDescription>Give it a name. Organisation, industry and use case are optional context.</DialogDescription>
        </DialogHeader>
        <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); if (valid) m.mutate(); }}>
          <div className="space-y-1.5">
            <Label htmlFor="na-title">Title</Label>
            <Input id="na-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="FinBank evaluation" maxLength={120} autoFocus />
            {title.length > 0 && !valid && <p className="text-xs text-red-700">3 to 120 characters.</p>}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="na-org">Organisation (optional)</Label>
              <Input id="na-org" value={org} onChange={(e) => setOrg(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="na-ind">Industry (optional)</Label>
              <Input id="na-ind" value={industry} onChange={(e) => setIndustry(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="na-uc">Intended use case (optional)</Label>
            <Textarea id="na-uc" rows={2} value={useCase} onChange={(e) => setUseCase(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={!valid || m.isPending}>Create</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
