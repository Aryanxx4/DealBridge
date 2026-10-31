import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Share2, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useUserKey } from "@/hooks/useIdentity";
import { sharingApi } from "@/services/sharing";
import type { Assessment } from "@/types/api";

const SEES = ["Assessment title, your organisation and your name", "Context: organisation, industry and use case", "The requirements in this version, with priority, category, source type and your quoted wording", "Statuses, explanations, evidence, assumptions, missing information and questions for the seller", "Seller responses and follow-up threads"];
const NEVER = ["Your uploaded files", "Chat transcripts (requirement chat and product chat)", "Questions you raised with the product team", "The raw guided-form answers", "Other versions you have not shared", "Any other buyer's data"];

export function ShareDialog({ assessment, versionNo, trigger, onShared }: { assessment: Assessment; versionNo?: number; trigger?: React.ReactNode; onShared?: (sellerOrgId: string) => void }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [org, setOrg] = useState("");
  const [consent, setConsent] = useState(false);
  const orgs = useQuery({ queryKey: ["seller-orgs", userKey], queryFn: sharingApi.sellerOrgs, enabled: open });
  const v = versionNo ?? assessment.latest_version_no;
  const m = useMutation({
    mutationFn: () => sharingApi.share(assessment.id, org, v),
    onSuccess: () => {
      toast.success(`Version ${v} shared`);
      qc.invalidateQueries({ queryKey: ["shares", userKey, assessment.id] });
      setOpen(false);
      setConsent(false);
      onShared?.(org);
    },
    onError: (e: Error) => toast.error(e.message),
  });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger ?? <Button variant="outline" disabled={!assessment.latest_version_no}><Share2 aria-hidden /> Share with seller</Button>}</DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Share version {v} with a seller</DialogTitle>
          <DialogDescription>Sharing is explicit and per version. You can revoke access at any time.</DialogDescription>
        </DialogHeader>
        {assessment.status === "STALE" && <Alert variant="warning"><AlertDescription>Your requirements changed after this version. The shared version does not include the latest edits.</AlertDescription></Alert>}
        <div className="space-y-1.5">
          <Label>Seller organisation</Label>
          <Select value={org} onValueChange={setOrg}>
            <SelectTrigger aria-label="Seller organisation"><SelectValue placeholder="Choose a seller" /></SelectTrigger>
            <SelectContent>{orgs.data?.map((o) => <SelectItem key={o.id} value={o.id}>{o.name}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <p className="font-semibold">The seller will see</p>
            <ul className="mt-1 space-y-1">{SEES.map((s) => <li key={s} className="flex gap-1.5"><Check className="mt-0.5 size-3.5 shrink-0 text-green-700" aria-hidden />{s}</li>)}</ul>
          </div>
          <div>
            <p className="font-semibold">The seller will never see</p>
            <ul className="mt-1 space-y-1">{NEVER.map((s) => <li key={s} className="flex gap-1.5"><X className="mt-0.5 size-3.5 shrink-0 text-red-700" aria-hidden />{s}</li>)}</ul>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <Checkbox id="share-consent" checked={consent} onCheckedChange={(c) => setConsent(c === true)} />
          <Label htmlFor="share-consent" className="leading-snug">I understand and consent to sharing this version with this seller</Label>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={() => m.mutate()} disabled={!org || !consent || m.isPending}>Share version {v}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
