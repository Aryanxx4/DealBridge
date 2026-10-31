import { ExternalLink } from "lucide-react";
import { useState } from "react";
import { cn, formatDate } from "@/lib/utils";
import type { Citation } from "@/types/api";
import { kindOf, SourceChip } from "./SourceChip";

/** One piece of evidence. Never shows a relevance score (scores are not evidence). */
export function EvidenceCard({ c, id, highlight }: { c: Citation; id?: string; highlight?: boolean }) {
  const [open, setOpen] = useState(false);
  const long = c.excerpt.length > 220;
  return (
    <div id={id} className={cn("rounded-lg border bg-card p-3 text-sm transition-shadow", highlight && "ring-2 ring-primary/60")}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded bg-slate-100 px-1.5 text-xs font-semibold text-slate-700">[{c.n}]</span>
        <SourceChip kind={kindOf(c.collection)} />
      </div>
      <p className="mt-2 font-medium">{c.title}</p>
      <p className="text-xs text-muted-foreground">{c.heading_path}</p>
      <blockquote className={cn("mt-2 border-l-2 border-indigo-200 pl-3 italic text-slate-700", !open && long && "line-clamp-3")}>“{c.excerpt}”</blockquote>
      {long && (
        <button type="button" className="mt-1 text-xs font-medium text-primary hover:underline" onClick={() => setOpen((v) => !v)}>
          {open ? "Show less" : "Show more"}
        </button>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
        {c.collection === "OFFICIAL" ? <span>Last verified {formatDate(c.last_verified_at)}</span> : <span>Approved {formatDate(c.approved_at)}</span>}
        {c.source_url && (
          <a href={c.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
            {c.source_document ?? "Source"} <ExternalLink className="size-3" aria-hidden />
          </a>
        )}
      </div>
    </div>
  );
}
