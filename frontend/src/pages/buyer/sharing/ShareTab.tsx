import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquarePlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { FollowUpStatusBadge, FollowUpThread } from "@/components/shared/FollowUpThread";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { cn, formatDateTime } from "@/lib/utils";
import { ApiError } from "@/services/api";
import { assessmentsApi } from "@/services/assessments";
import { sharingApi } from "@/services/sharing";
import type { Assessment } from "@/types/api";
import { ShareDialog } from "./ShareDialog";

export function ShareTab({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const shares = useQuery({ queryKey: ["shares", userKey, assessment.id], queryFn: () => sharingApi.shares(assessment.id) });
  const followUps = useQuery({ queryKey: ["follow-ups", userKey, assessment.id], queryFn: () => sharingApi.followUps(assessment.id) });
  const [openThread, setOpenThread] = useState<string | null>(null);
  const revoke = useMutation({
    mutationFn: (org: string) => sharingApi.unshare(assessment.id, org),
    onSuccess: () => { toast.success("Access revoked"); qc.invalidateQueries({ queryKey: ["shares", userKey, assessment.id] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  const active = (shares.data ?? []).filter((s) => s.active);
  const activeOrgs = [...new Map(active.map((s) => [s.seller_org_id, s.seller_org])).entries()];
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
          <CardTitle className="text-base">Sharing</CardTitle>
          <ShareDialog assessment={assessment} />
        </CardHeader>
        <CardContent>
          {!assessment.latest_version_no && <p className="text-sm text-muted-foreground">Run the assessment before sharing. Only analysed versions can be shared.</p>}
          {shares.isLoading && <LoadingRows rows={2} />}
          {shares.error && <ErrorState error={shares.error} onRetry={() => shares.refetch()} />}
          {shares.data?.length === 0 && assessment.latest_version_no > 0 && <p className="text-sm text-muted-foreground">Private: not shared with anyone.</p>}
          <ul className="divide-y text-sm">
            {shares.data?.map((s) => (
              <li key={s.id} className={cn("flex flex-wrap items-center gap-3 py-2", !s.active && "text-muted-foreground")}>
                <span className="font-medium">{s.seller_org}</span>
                <span>version {s.version_no}</span>
                <span className="text-xs">shared {formatDateTime(s.shared_at)}</span>
                {s.active ? <span className="rounded-md border border-green-200 bg-green-50 px-1.5 text-xs text-green-800">Active</span> : <span className="text-xs">revoked {formatDateTime(s.revoked_at)}</span>}
              </li>
            ))}
          </ul>
          {activeOrgs.map(([orgId, name]) => (
            <ConfirmDialog key={orgId} trigger={<Button size="sm" variant="outline" className="mt-2 text-red-700">Revoke access for {name}</Button>} title={`Revoke ${name}'s access?`} description="They immediately lose access to every shared version and to follow-up threads." confirmLabel="Revoke access" destructive onConfirm={() => revoke.mutateAsync(orgId)} />
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
          <CardTitle className="text-base">Follow-ups</CardTitle>
          <RequestFollowUp assessment={assessment} activeOrgs={activeOrgs} />
        </CardHeader>
        <CardContent className="space-y-3">
          {followUps.isLoading && <LoadingRows rows={2} />}
          {followUps.data?.length === 0 && <EmptyState title="No follow-ups yet" description="Request a follow-up to ask the seller about gaps or unknowns." />}
          <ul className="space-y-2">
            {followUps.data?.map((f) => (
              <li key={f.id} className="rounded-lg border">
                <button type="button" className="flex w-full flex-wrap items-center gap-2 p-3 text-left" onClick={() => setOpenThread(openThread === f.id ? null : f.id)} aria-expanded={openThread === f.id}>
                  <span className="font-medium">{f.subject}</span>
                  <FollowUpStatusBadge status={f.status} />
                  <span className="ml-auto text-xs text-muted-foreground">{f.seller_org} · updated {formatDateTime(f.updated_at)}</span>
                </button>
                {openThread === f.id && <div className="border-t p-3"><FollowUpThread id={f.id} /></div>}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function RequestFollowUp({ assessment, activeOrgs }: { assessment: Assessment; activeOrgs: [string, string][] }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [org, setOrg] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [reqs, setReqs] = useState<string[]>([]);
  const requirements = useQuery({ queryKey: ["requirements", userKey, assessment.id, false], queryFn: () => assessmentsApi.requirements(assessment.id), enabled: open });
  const orgs = useQuery({ queryKey: ["seller-orgs", userKey], queryFn: sharingApi.sellerOrgs, enabled: open });
  const shared = activeOrgs.some(([id]) => id === org);
  const m = useMutation({
    mutationFn: () => sharingApi.createFollowUp(assessment.id, { seller_org_id: org, subject: subject.trim(), message: message.trim(), related_requirement_ids: reqs }),
    onSuccess: () => { toast.success("Follow-up requested"); qc.invalidateQueries({ queryKey: ["follow-ups", userKey, assessment.id] }); setOpen(false); setSubject(""); setMessage(""); setReqs([]); },
    onError: (e) => toast.error(e instanceof ApiError && e.code === "NOT_SHARED" ? "Share the assessment with this seller first." : (e as Error).message),
  });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild><Button disabled={!assessment.latest_version_no}><MessageSquarePlus aria-hidden /> Request follow-up</Button></DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Request a follow-up</DialogTitle>
          <DialogDescription>The seller sees the shared version, this message and the selected requirements.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Seller organisation</Label>
            <Select value={org} onValueChange={setOrg}>
              <SelectTrigger aria-label="Seller organisation"><SelectValue placeholder="Choose a seller" /></SelectTrigger>
              <SelectContent>{orgs.data?.map((o) => <SelectItem key={o.id} value={o.id}>{o.name}</SelectItem>)}</SelectContent>
            </Select>
            {org && !shared && (
              <div className="flex flex-wrap items-center gap-2 rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900">
                Not shared with this seller yet. Sharing requires your explicit consent.
                <ShareDialog assessment={assessment} trigger={<Button size="sm" variant="outline">Share first…</Button>} onShared={() => qc.invalidateQueries({ queryKey: ["shares", userKey, assessment.id] })} />
              </div>
            )}
          </div>
          <div className="space-y-1.5"><Label htmlFor="fu-subj">Subject</Label><Input id="fu-subj" value={subject} maxLength={200} onChange={(e) => setSubject(e.target.value)} /></div>
          <div className="space-y-1.5"><Label htmlFor="fu-msg">Message</Label><Textarea id="fu-msg" rows={3} maxLength={4000} value={message} onChange={(e) => setMessage(e.target.value)} /></div>
          <div className="space-y-1.5">
            <Label>Related requirements (optional)</Label>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-md border p-2">
              {requirements.data?.map((r) => (
                <label key={r.id} className="flex items-start gap-2 text-sm">
                  <Checkbox checked={reqs.includes(r.id)} onCheckedChange={(c) => setReqs((s) => (c ? [...s, r.id] : s.filter((x) => x !== r.id)))} aria-label={r.display_id} />
                  <span><span className="font-mono text-xs">{r.display_id}</span> {r.normalized_text}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={() => m.mutate()} disabled={!org || !shared || subject.trim().length < 3 || m.isPending}>Send request</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
