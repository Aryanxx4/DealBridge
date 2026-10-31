import { useSearchParams } from "react-router-dom";
import { RequireRole } from "@/components/layout/RequireRole";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OfficialKnowledgeTab } from "./OfficialKnowledgeTab";
import { ResolvedKnowledgeTab } from "./ResolvedKnowledgeTab";

export function KnowledgePage() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") ?? "official";
  return (
    <RequireRole roles={["ADMIN"]}>
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-semibold">Knowledge</h1>
          <p className="text-sm text-muted-foreground">Official documentation (OKF bundle) and approved expert answers, indexed separately.</p>
        </div>
        <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
          <TabsList>
            <TabsTrigger value="official">Official knowledge</TabsTrigger>
            <TabsTrigger value="resolved">Resolved knowledge</TabsTrigger>
          </TabsList>
          <TabsContent value="resolved">
            <ResolvedKnowledgeTab />
          </TabsContent>
          <TabsContent value="official">
            <OfficialKnowledgeTab />
          </TabsContent>
        </Tabs>
      </div>
    </RequireRole>
  );
}
