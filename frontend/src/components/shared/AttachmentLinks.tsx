import { Paperclip } from "lucide-react";
import { toast } from "sonner";
import { sharingApi } from "@/services/sharing";
import type { Attachment } from "@/types/api";

/** Seller-provided documents: downloadable, clearly labelled, never treated as official knowledge. */
export function AttachmentLinks({ items }: { items?: Attachment[] }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-1 space-y-0.5">
      {items.map((a) => (
        <li key={a.id}>
          <button type="button" className="inline-flex items-center gap-1 text-xs text-teal-800 underline" onClick={() => sharingApi.downloadDocument(a.id, a.filename).catch((e: Error) => toast.error(e.message))}>
            <Paperclip className="size-3" aria-hidden /> {a.filename}
          </button>
          <span className="ml-1 text-[11px] text-muted-foreground">({a.label})</span>
        </li>
      ))}
    </ul>
  );
}
