import { Info } from "lucide-react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useIdentity } from "@/hooks/useIdentity";
import { cn } from "@/lib/utils";
import { HealthIndicator } from "./HealthIndicator";
import { NAV_ITEMS } from "./navigation";
import { RoleSwitcher } from "./RoleSwitcher";

export function AppShell() {
  const { user } = useIdentity();
  const items = user ? NAV_ITEMS.filter((i) => i.roles.includes(user.role)) : [];
  const loc = useLocation();
  const isActive = (to: string) => {
    const [path, query] = to.split("?");
    if (query) return loc.pathname === path && loc.search.includes(query);
    const sibling = items.some((i) => i.to !== to && i.to.startsWith(`${path}?`) && loc.pathname === path && loc.search.includes(i.to.split("?")[1]));
    if (sibling) return false;
    return path === "/admin" || path === "/seller" || path === "/buyer" || path === "/chat" ? loc.pathname === path || (path !== "/chat" && loc.pathname.startsWith(`${path}/`) && !items.some((i) => i.to !== to && loc.pathname.startsWith(i.to))) : loc.pathname.startsWith(path);
  };
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex items-center justify-center gap-2 bg-slate-900 px-4 py-1.5 text-center text-xs text-slate-100" role="note">
        <Info className="size-3.5 shrink-0" aria-hidden />
        Demo identities only. This is not authentication.
      </div>
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
          <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
            <img src="/favicon.svg" alt="" className="size-7" />
            DealBridge
          </Link>
          <nav className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto" aria-label="Main">
            {items.map((i) => (
              <Link
                key={i.to}
                to={i.to}
                aria-current={isActive(i.to) ? "page" : undefined}
                className={cn("whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-slate-100 hover:text-foreground", isActive(i.to) && "bg-accent text-accent-foreground")}
              >
                {i.label}
              </Link>
            ))}
          </nav>
          <HealthIndicator />
          <RoleSwitcher />
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
