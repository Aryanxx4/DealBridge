import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { RequireRole } from "@/components/layout/RequireRole";
import { FollowUpThread } from "@/components/shared/FollowUpThread";
import { Card, CardContent } from "@/components/ui/card";

export function SellerFollowUpPage() {
  const { id = "" } = useParams();
  return (
    <RequireRole roles={["SELLER"]}>
      <div className="space-y-4">
        <Link to="/seller?tab=followups" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" aria-hidden /> Follow-ups</Link>
        <Card><CardContent className="pt-5"><FollowUpThread id={id} /></CardContent></Card>
      </div>
    </RequireRole>
  );
}
