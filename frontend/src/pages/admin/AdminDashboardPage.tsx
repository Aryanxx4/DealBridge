import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RequireRole } from "@/components/layout/RequireRole";
import { EmptyState, ErrorState, LoadingRows } from "@/components/shared/States";
import { TicketStatusBadge } from "@/components/shared/TicketStatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useUserKey } from "@/hooks/useIdentity";
import { formatDateTime } from "@/lib/utils";
import { adminApi } from "@/services/admin";

const FILTERS = [
  { value: "active", label: "Needs attention", status: "OPEN,IN_REVIEW,ANSWER_PROPOSED,APPROVED" },
  { value: "OPEN", label: "Open", status: "OPEN" },
  { value: "IN_REVIEW", label: "In review", status: "IN_REVIEW" },
  { value: "ANSWER_PROPOSED", label: "Awaiting approval", status: "ANSWER_PROPOSED" },
  { value: "PUBLISHED", label: "Published", status: "PUBLISHED" },
  { value: "REJECTED", label: "Rejected", status: "REJECTED" },
  { value: "CLOSED", label: "Closed", status: "CLOSED" },
  { value: "all", label: "All", status: "" },
];

export function AdminDashboardPage() {
  return (
    <RequireRole roles={["ADMIN"]}>
      <Dashboard />
    </RequireRole>
  );
}

function Dashboard() {
  const userKey = useUserKey();
  const navigate = useNavigate();
  const [filter, setFilter] = useState("active");
  const [category, setCategory] = useState("all");
  const status = FILTERS.find((f) => f.value === filter)?.status ?? "";
  const dash = useQuery({ queryKey: ["admin-dashboard", userKey], queryFn: adminApi.dashboard });
  const tickets = useQuery({ queryKey: ["admin-tickets", userKey, status, category], queryFn: () => adminApi.tickets(status || undefined, category === "all" ? undefined : category) });
  const audit = useQuery({ queryKey: ["admin-audit", userKey], queryFn: () => adminApi.audit(15) });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Admin dashboard</h1>
        <p className="text-sm text-muted-foreground">Unanswered product questions and the knowledge they become. All numbers are live counts.</p>
      </div>
      {dash.error ? (
        <ErrorState error={dash.error} onRetry={() => dash.refetch()} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Tile label="Open tickets" value={dash.data?.tickets.open} />
          <Tile label="In review" value={dash.data?.tickets.in_review} />
          <Tile label="Awaiting approval" value={dash.data?.tickets.awaiting_approval} />
          <Tile label="Published expert answers" value={dash.data?.published_knowledge_records} />
          <Tile label="Official files indexed" value={dash.data?.official_files_indexed} />
          <Tile label="Official chunks" value={dash.data ? (dash.data.official_chunks ?? "unavailable") : undefined} />
        </div>
      )}
      <Card>
        <CardHeader className="flex-row items-center justify-between gap-3 space-y-0">
          <CardTitle className="text-base">Ticket queue</CardTitle>
          <div className="flex flex-wrap gap-2">
          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger className="w-44" aria-label="Filter tickets by category">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              {["deployment", "architecture", "security", "platform", "integrations", "concepts", "OTHER"].map((c) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-48" aria-label="Filter tickets by status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {FILTERS.map((f) => (
                <SelectItem key={f.value} value={f.value}>
                  {f.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {tickets.isLoading && <div className="p-4"><LoadingRows /></div>}
          {tickets.error && <div className="p-4"><ErrorState error={tickets.error} onRetry={() => tickets.refetch()} /></div>}
          {tickets.data?.length === 0 && <div className="p-4"><EmptyState title="No tickets here" description="Questions the chatbot cannot verify will appear in this queue." /></div>}
          {!!tickets.data?.length && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ticket</TableHead>
                  <TableHead>Question</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Asked</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tickets.data.map((t) => (
                  <TableRow key={t.id} className="cursor-pointer" onClick={() => navigate(`/admin/tickets/${t.id}`)}>
                    <TableCell className="font-mono text-xs">
                      <a href={`/admin/tickets/${t.id}`} onClick={(e) => { e.preventDefault(); navigate(`/admin/tickets/${t.id}`); }} className="text-primary hover:underline">
                        {t.display_id}
                      </a>
                    </TableCell>
                    <TableCell className="max-w-md truncate">{t.normalised_question}</TableCell>
                    <TableCell><TicketStatusBadge status={t.status} /></TableCell>
                    <TableCell className="text-right tabular-nums">{t.occurrence_count}×</TableCell>
                    <TableCell className="text-xs">{t.priority}</TableCell>
                    <TableCell className="whitespace-nowrap text-xs">{formatDateTime(t.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          {audit.isLoading && <LoadingRows />}
          {audit.data?.length === 0 && <p className="text-sm text-muted-foreground">No activity yet.</p>}
          <ul className="divide-y text-sm">
            {audit.data?.map((e) => (
              <li key={e.id} className="flex flex-wrap items-center gap-x-3 py-2">
                <span className="font-medium">{e.action.replaceAll("_", " ").toLowerCase()}</span>
                <span className="text-muted-foreground">{e.actor ?? "system"}</span>
                <span className="ml-auto text-xs text-muted-foreground">{formatDateTime(e.created_at)}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function Tile({ label, value }: { label: string; value: number | string | undefined }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value ?? "…"}</p>
    </div>
  );
}
