import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { RequireRole } from "@/components/layout/RequireRole";
import { AssessmentStatusBadge } from "@/components/shared/Badges";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUserKey } from "@/hooks/useIdentity";
import { assessmentsApi } from "@/services/assessments";
import { RequirementsTab } from "./requirements/RequirementsTab";
import { WORKSPACE_TABS } from "./workspaceTabs";

export function AssessmentWorkspacePage() {
  return (
    <RequireRole roles={["BUYER"]}>
      <Inner />
    </RequireRole>
  );
}

function Inner() {
  const { id = "" } = useParams();
  const userKey = useUserKey();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") ?? "requirements";
  const q = useQuery({ queryKey: ["assessment", userKey, id], queryFn: () => assessmentsApi.get(id), refetchInterval: (query) => (query.state.data?.status === "ANALYZING" ? 3000 : false) });
  if (q.isLoading) return <LoadingRows rows={5} />;
  if (q.error) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const a = q.data!;
  return (
    <div className="space-y-4">
      <Link to="/buyer" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" aria-hidden /> All assessments
      </Link>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold">{a.title}</h1>
        <AssessmentStatusBadge status={a.status} />
        {a.context.organisation_name && <span className="text-sm text-muted-foreground">{a.context.organisation_name}{a.context.industry ? ` · ${a.context.industry}` : ""}</span>}
      </div>
      {a.status === "STALE" && (
        <Alert variant="warning">
          <AlertTriangle aria-hidden />
          <AlertDescription>Requirements changed after the last assessment, so the results are out of date. Re-run the assessment to update them.</AlertDescription>
        </Alert>
      )}
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          {WORKSPACE_TABS.map((t) => (
            <TabsTrigger key={t.value} value={t.value}>
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="requirements">
          <RequirementsTab assessment={a} />
        </TabsContent>
        {WORKSPACE_TABS.map((t) => (
          <TabsContent key={t.value} value={t.value}>
            <t.Component assessment={a} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
