import { useQuery } from "@tanstack/react-query";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { identityApi } from "@/services/identity";
import { cn } from "@/lib/utils";

export function HealthIndicator() {
  const q = useQuery({ queryKey: ["health"], queryFn: identityApi.health, refetchInterval: 30_000, retry: false });
  const h = q.data;
  let tone = "bg-slate-400";
  let label = "Checking services…";
  const problems: string[] = [];
  if (q.isError) {
    tone = "bg-red-500";
    label = "API unreachable";
  } else if (h) {
    if (!h.dependencies.postgres.ok) problems.push("PostgreSQL unavailable");
    if (!h.dependencies.qdrant.ok) problems.push("Vector database unavailable");
    if (!h.dependencies.embedding_model.ok) problems.push(h.embedding_loading ? "Embedding model loading" : "Embedding model unavailable");
    if (!h.dependencies.llm.configured) problems.push("LLM API key not configured — AI features disabled");
    if (h.reindex_required) problems.push("Knowledge reindex required");
    tone = problems.length ? "bg-amber-500" : "bg-green-600";
    label = problems.length ? "Degraded" : "All services healthy";
  }
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button type="button" className="flex items-center gap-2 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-slate-100" aria-label={`Service status: ${label}`}>
          <span className={cn("size-2.5 rounded-full", tone)} aria-hidden />
          <span className="hidden md:inline">{label}</span>
        </button>
      </TooltipTrigger>
      <TooltipContent>{problems.length ? problems.join(" · ") : label}</TooltipContent>
    </Tooltip>
  );
}
