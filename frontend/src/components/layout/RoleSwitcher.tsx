import { ChevronDown, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useIdentity } from "@/hooks/useIdentity";

const ROLE_LABEL = { BUYER: "Buyer", SELLER: "Seller", ADMIN: "Admin" } as const;

export function RoleSwitcher() {
  const { user, users, switchTo } = useIdentity();
  const navigate = useNavigate();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" aria-label="Switch demo identity">
          <UserRound aria-hidden />
          <span className="max-w-[10rem] truncate">{user ? `${user.display_name} · ${ROLE_LABEL[user.role]}` : "Choose identity"}</span>
          <ChevronDown aria-hidden />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel>Demo identities (not authentication)</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {users.map((u) => (
          <DropdownMenuItem
            key={u.id}
            onSelect={() => {
              switchTo(u.id);
              navigate("/");
            }}
          >
            <div className="min-w-0">
              <p className="truncate font-medium">
                {u.display_name} {u.id === user?.id && <span className="text-xs text-primary">(current)</span>}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {ROLE_LABEL[u.role]} · {u.organization.name}
              </p>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
