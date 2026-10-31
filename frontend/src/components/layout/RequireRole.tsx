import { ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
import { EmptyState, LoadingRows } from "@/components/shared/States";
import { useIdentity } from "@/hooks/useIdentity";
import type { UserRole } from "@/types/api";
import { RoleSwitcher } from "./RoleSwitcher";

export function RequireRole({ roles, children }: { roles: UserRole[]; children: ReactNode }) {
  const { user, loading } = useIdentity();
  if (loading) return <LoadingRows />;
  if (!user || !roles.includes(user.role)) {
    return (
      <EmptyState
        icon={<ShieldAlert className="size-8" aria-hidden />}
        title="Not available for your role"
        description={`This page is for ${roles.map((r) => r.toLowerCase()).join(" or ")} identities. Switch to a different demo identity to continue.`}
        action={<RoleSwitcher />}
      />
    );
  }
  return <>{children}</>;
}
