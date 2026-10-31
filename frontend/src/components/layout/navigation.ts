import type { UserRole } from "@/types/api";

export interface NavItem {
  label: string;
  to: string;
  roles: UserRole[];
}

// Only features that exist are listed (no placeholder pages). Items are added as each gate lands.
export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", to: "/admin", roles: ["ADMIN"] },
  { label: "Knowledge", to: "/admin/knowledge", roles: ["ADMIN"] },
  { label: "Product chat", to: "/chat", roles: ["BUYER", "SELLER", "ADMIN"] },
  { label: "My questions", to: "/chat/questions", roles: ["BUYER"] },
];
