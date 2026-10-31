import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";
import { getStoredUserId, storeUserId } from "@/services/api";
import { identityApi } from "@/services/identity";
import type { DemoUser } from "@/types/api";

interface IdentityContextValue {
  user: DemoUser | null;
  users: DemoUser[];
  loading: boolean;
  error: unknown;
  switchTo: (id: string) => void;
}

const IdentityContext = createContext<IdentityContextValue | null>(null);

export function IdentityProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [userId, setUserId] = useState<string | null>(() => getStoredUserId());
  const usersQ = useQuery({ queryKey: ["identity-users"], queryFn: identityApi.users, staleTime: 60_000 });
  const users = useMemo(() => usersQ.data ?? [], [usersQ.data]);
  const user = users.find((u) => u.id === userId) ?? null;

  const switchTo = useCallback(
    (id: string) => {
      storeUserId(id);
      setUserId(id);
      // Never show one identity another identity's cached data.
      qc.removeQueries({ predicate: (q) => q.queryKey[0] !== "identity-users" && q.queryKey[0] !== "health" });
    },
    [qc],
  );

  const value = useMemo(
    () => ({ user, users, loading: usersQ.isLoading, error: usersQ.error, switchTo }),
    [user, users, usersQ.isLoading, usersQ.error, switchTo],
  );
  return <IdentityContext.Provider value={value}>{children}</IdentityContext.Provider>;
}

export function useIdentity(): IdentityContextValue {
  const ctx = useContext(IdentityContext);
  if (!ctx) throw new Error("useIdentity must be used inside IdentityProvider");
  return ctx;
}

/** Query key prefix that scopes cached data to the current demo user. */
export function useUserKey(): string {
  return useIdentity().user?.id ?? "anonymous";
}
