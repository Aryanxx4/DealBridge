import { FileUp, ListChecks, MessageSquare } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { LlmStatusAlert } from "@/components/shared/LlmStatusAlert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Assessment } from "@/types/api";
import { GuidedFormPanel } from "./GuidedFormPanel";
import { IntakeChatPanel } from "./IntakeChatPanel";
import { RequirementsFooter } from "./RequirementsFooter";
import { ReviewTable } from "./ReviewTable";
import { UploadPdfPanel } from "./UploadPdfPanel";

export function RequirementsTab({ assessment }: { assessment: Assessment }) {
  const [params, setParams] = useSearchParams();
  const mode = params.get("add") ?? "pdf";
  return (
    <div className="space-y-6 pb-20">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add requirements</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <LlmStatusAlert feature="Reading PDFs, the requirement chat and the free-text form fields" />
          <Tabs value={mode} onValueChange={(v) => setParams((p) => { p.set("add", v); return p; }, { replace: true })}>
            <TabsList>
              <TabsTrigger value="pdf"><FileUp aria-hidden /> Upload PDF</TabsTrigger>
              <TabsTrigger value="chat"><MessageSquare aria-hidden /> Chat</TabsTrigger>
              <TabsTrigger value="form"><ListChecks aria-hidden /> Guided form</TabsTrigger>
            </TabsList>
            <TabsContent value="pdf"><UploadPdfPanel assessment={assessment} /></TabsContent>
            <TabsContent value="chat"><IntakeChatPanel assessment={assessment} /></TabsContent>
            <TabsContent value="form"><GuidedFormPanel assessment={assessment} /></TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      <ReviewTable assessment={assessment} />
      <RequirementsFooter assessment={assessment} />
    </div>
  );
}
