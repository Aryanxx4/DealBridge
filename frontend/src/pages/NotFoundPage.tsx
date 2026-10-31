import { Link } from "react-router-dom";
import { EmptyState } from "@/components/shared/States";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return <EmptyState title="Page not found" description="This page does not exist." action={<Button asChild variant="outline"><Link to="/">Go home</Link></Button>} />;
}
