import { useQuery } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { identityApi } from "@/services/identity";

/** Shown wherever a feature needs the LLM and the backend reports it is not configured. */
export function LlmStatusAlert({ feature }: { feature: string }) {
  const q = useQuery({ queryKey: ["health"], queryFn: identityApi.health, refetchInterval: 30_000, retry: false });
  if (!q.data || q.data.dependencies.llm.configured) return null;
  return (
    <Alert variant="warning">
      <KeyRound aria-hidden />
      <AlertTitle>Language model not configured</AlertTitle>
      <AlertDescription>{feature} needs the LLM. Set LLM_API_KEY in the backend .env and restart the backend. Nothing is answered without it.</AlertDescription>
    </Alert>
  );
}
