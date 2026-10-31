import { AlertTriangle, MessageCircleQuestion, Sparkles, Wand2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PriorityBadge } from "@/components/shared/Badges";
import { EvidenceCard } from "@/components/shared/EvidenceCard";
import { SourceChip } from "@/components/shared/SourceChip";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { TicketStatusBadge } from "@/components/shared/TicketStatusBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { formatDateTime } from "@/lib/utils";
import { CATEGORY_LABELS, type RequirementResult } from "@/types/api";

export const ASSERTION_LABELS = {
  NONE: "Comment",
  CONFIRMS_SUPPORT: "Confirms support",
  CONFIRMS_LIMITATION: "Confirms a limitation",
  NEEDS_INFO_FROM_BUYER: "Needs information from the buyer",
} as const;

export function RequirementDetailSheet({ item, assessmentId, onClose, sellerSlot, hideAsk }: { item: RequirementResult | null; assessmentId: string; onClose: () => void; sellerSlot?: React.ReactNode; hideAsk?: boolean }) {
  const navigate = useNavigate();
  const ask = (i: RequirementResult) => {
    const q = `Does IOMETE meet this requirement: ${i.text}`;
    navigate(`/chat?assessment=${assessmentId}&requirement=${i.requirement_id}&q=${encodeURIComponent(q)}`);
  };
  return (
    <Sheet open={!!item} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="sm:max-w-2xl">
        {item && (
          <>
            <SheetHeader>
              <SheetTitle className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm text-muted-foreground">{item.display_id}</span>
                <StatusBadge status={item.status} />
                <PriorityBadge priority={item.priority} />
              </SheetTitle>
              <SheetDescription>{item.text}</SheetDescription>
            </SheetHeader>
            <p className="text-xs text-muted-foreground">
              {CATEGORY_LABELS[item.category]}
              {item.source_quote && item.source_quote !== item.text && <> · buyer's words: “{item.source_quote}”{item.source_page ? ` (page ${item.source_page})` : ""}</>}
            </p>
            {item.answer_available && (
              <Alert variant="info"><Sparkles aria-hidden /><AlertDescription>An expert answer is now available for the open question. Re-run the assessment to use it.</AlertDescription></Alert>
            )}
            <section className="space-y-3 text-sm">
              <Field label="System assessment" value={<StatusBadge status={item.status} />} />
              <Field label="What it means" value={item.explanation.meaning} />
              <Field label="What the evidence establishes" value={item.explanation.established} />
              <Field label="What remains unverified" value={item.explanation.unverified} />
              {item.status === "PARTIALLY_SUPPORTED" && (
                <div className="grid gap-2 sm:grid-cols-2">
                  <Field label="Supported part" value={item.supported_part} />
                  <Field label="Not established" value={item.unestablished_part} />
                </div>
              )}
              {item.explanation.next_step && <Field label="Next step" value={item.explanation.next_step} />}
              {item.has_conflict && (
                <Alert variant="warning"><AlertTriangle aria-hidden /><AlertDescription><strong>Sources conflict.</strong> {item.conflict_description}</AlertDescription></Alert>
              )}
            </section>
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">Evidence ({item.evidence.length})</h3>
              {item.evidence.length === 0 ? (
                <p className="text-sm text-muted-foreground">No cited excerpt establishes this requirement{item.candidate_count === 0 ? " (no relevant product knowledge was retrieved)" : ""}.</p>
              ) : (
                item.evidence.map((e) => (
                  <div key={e.rank}>
                    <p className="mb-1 text-xs font-medium text-muted-foreground">{e.role === "SUPPORTS" ? "Supports" : e.role === "LIMITS" ? "States a limitation" : "Related context"}</p>
                    <EvidenceCard c={{ ...e, n: e.rank, heading_path: e.heading_path ?? "" }} />
                  </div>
                ))
              )}
            </section>
            {!!item.missing_information.length && <ListSection title="Missing information" items={item.missing_information} />}
            {!!item.assumptions.length && <ListSection title="Assumptions" items={item.assumptions} />}
            {!!item.questions_for_seller.length && <ListSection title="Questions for the seller" items={item.questions_for_seller} />}
            {!!item.guardrail_notes.length && (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                <p className="flex items-center gap-1 font-semibold"><Wand2 className="size-4" aria-hidden /> Adjusted automatically</p>
                <ul className="mt-1 list-disc pl-5 text-slate-700">{item.guardrail_notes.map((n) => <li key={n}>{n}</li>)}</ul>
              </div>
            )}
            <section className="space-y-2">
              <h3 className="text-sm font-semibold">Seller responses</h3>
              {item.seller_responses.length === 0 && <p className="text-sm text-muted-foreground">No seller response.</p>}
              {item.seller_responses.map((s) => (
                <div key={s.id} className="space-y-1 rounded-md border border-teal-200 bg-teal-50/50 p-3 text-sm">
                  <p className="text-xs">System assessment: <strong>{item.status.replaceAll("_", " ").toLowerCase()}</strong></p>
                  <div className="flex flex-wrap items-center gap-2">
                    <SourceChip kind="seller" />
                    <span className="text-xs text-muted-foreground">Seller response (attributed, not verified by documentation) · {s.seller_name}, {s.seller_org} · {formatDateTime(s.created_at)}</span>
                  </div>
                  <p><strong>{ASSERTION_LABELS[s.assertion]}:</strong> {s.body}</p>
                </div>
              ))}
              {sellerSlot}
            </section>
            {item.open_ticket && (
              <p className="flex items-center gap-2 text-sm">Open question with the product team: <strong>{item.open_ticket.display_id}</strong> <TicketStatusBadge status={item.open_ticket.status} /></p>
            )}
            {!hideAsk && ["UNKNOWN", "NEEDS_VALIDATION", "PARTIALLY_SUPPORTED"].includes(item.status) && !item.open_ticket && (
              <Button variant="outline" onClick={() => ask(item)}><MessageCircleQuestion aria-hidden /> Ask the product team</Button>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="mt-0.5">{value}</div>
    </div>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">{items.map((i) => <li key={i}>{i}</li>)}</ul>
    </section>
  );
}
