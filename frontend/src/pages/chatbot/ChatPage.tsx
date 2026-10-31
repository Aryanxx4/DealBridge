import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, MessageSquarePlus, Send, ShieldCheck, Ticket as TicketIcon } from "lucide-react";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { AnswerTypeBadge } from "@/components/shared/AnswerTypeBadge";
import { EvidenceCard } from "@/components/shared/EvidenceCard";
import { LlmStatusAlert } from "@/components/shared/LlmStatusAlert";
import { Markdown } from "@/components/shared/Markdown";
import { SourceChip } from "@/components/shared/SourceChip";
import { ErrorState, LoadingRows } from "@/components/shared/States";
import { TicketStatusBadge } from "@/components/shared/TicketStatusBadge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useIdentity, useUserKey } from "@/hooks/useIdentity";
import { cn } from "@/lib/utils";
import { myQuestionsApi } from "@/services/admin";
import { chatApi } from "@/services/chat";
import type { ChatMessage, TicketStatus } from "@/types/api";

const FINAL: TicketStatus[] = ["PUBLISHED", "CLOSED", "REJECTED"];

const MAX = 2000;
const PRIVACY = "Questions I cannot verify are shared with the product team for review. Your assessments and documents are not shared.";

export function ChatPage() {
  const { user } = useIdentity();
  const userKey = useUserKey();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const sessionId = params.get("s");
  const linkAssessment = params.get("assessment");
  const linkRequirement = params.get("requirement");
  const [draft, setDraft] = useState(() => params.get("q") ?? "");
  const [pending, setPending] = useState<string | null>(null);
  const [failed, setFailed] = useState<{ question: string; error: unknown } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const sessions = useQuery({ queryKey: ["chat-sessions", userKey], queryFn: chatApi.sessions, enabled: !!user });
  const detail = useQuery({ queryKey: ["chat-session", userKey, sessionId], queryFn: () => chatApi.session(sessionId!), enabled: !!user && !!sessionId });
  const suggested = useQuery({ queryKey: ["chat-suggested", userKey], queryFn: chatApi.suggested, enabled: !!user, staleTime: 300_000 });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [detail.data?.messages.length, pending]);

  const send = useMutation({
    mutationFn: async (question: string) => {
      let sid = sessionId;
      if (!sid) {
        const s = await chatApi.create({ assessment_id: linkAssessment, requirement_id: linkRequirement });
        sid = s.id;
        setParams({ s: sid }, { replace: true });
      }
      return { sid, res: await chatApi.send(sid, question) };
    },
    onMutate: (question) => {
      setPending(question);
      setFailed(null);
      setDraft("");
    },
    onSuccess: ({ sid }) => {
      qc.invalidateQueries({ queryKey: ["chat-session", userKey, sid] });
      qc.invalidateQueries({ queryKey: ["chat-sessions", userKey] });
    },
    onError: (error, question) => {
      setFailed({ question, error });
      if (sessionId) qc.invalidateQueries({ queryKey: ["chat-session", userKey, sessionId] });
    },
    onSettled: () => setPending(null),
  });

  const submit = (text: string) => {
    const q = text.trim();
    if (!q || q.length > MAX || send.isPending) return;
    send.mutate(q);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(draft);
    }
  };

  const newChat = () => {
    setParams({}, { replace: false });
    setDraft("");
    setFailed(null);
  };

  const messages = detail.data?.messages ?? [];
  const hasOpenTicket = messages.some((m) => m.ticket && !FINAL.includes(m.ticket.status));
  const myTickets = useQuery({
    queryKey: ["my-tickets", userKey],
    queryFn: myQuestionsApi.list,
    enabled: !!user && hasOpenTicket,
    refetchInterval: hasOpenTicket ? 10_000 : false,
  });
  const liveStatus = new Map(myTickets.data?.map((t) => [t.id, t.status]) ?? []);

  if (!user) return <ErrorState error={new Error("Choose a demo identity to use the product chat.")} title="No identity selected" />;
  const showWelcome = !sessionId || (detail.isSuccess && messages.length === 0 && !pending);

  return (
    <div className="grid gap-4 md:grid-cols-[15rem_1fr]">
      <aside className="space-y-2" aria-label="Chat sessions">
        <Button className="w-full" variant="outline" onClick={newChat}>
          <MessageSquarePlus aria-hidden /> New chat
        </Button>
        <Link to="/chat/questions" className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-muted-foreground hover:bg-slate-100">
          <TicketIcon className="size-4" aria-hidden /> My questions
        </Link>
        <div className="max-h-[60vh] space-y-1 overflow-y-auto">
          {sessions.isLoading && <LoadingRows rows={3} />}
          {sessions.data?.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setParams({ s: s.id })}
              className={cn("w-full truncate rounded-md px-2 py-1.5 text-left text-sm hover:bg-slate-100", s.id === sessionId && "bg-accent font-medium text-accent-foreground")}
            >
              {s.title}
            </button>
          ))}
          {sessions.data?.length === 0 && <p className="px-2 text-xs text-muted-foreground">No conversations yet.</p>}
        </div>
      </aside>

      <section className="flex min-h-[70vh] min-w-0 flex-col gap-0 rounded-lg border bg-card">
        <div className="empty:hidden p-3 pb-0">
          <LlmStatusAlert feature="Answering questions" />
        </div>
        {linkAssessment && !sessionId && (
          <div className="border-b bg-indigo-50 px-4 py-2 text-xs text-indigo-900">
            This chat is linked to your assessment. If the question can't be verified, the ticket is attached to that requirement. Your assessment content is not sent.
          </div>
        )}
        <div className="flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
          {sessionId && detail.isLoading && <LoadingRows rows={3} />}
          {detail.error && <ErrorState error={detail.error} onRetry={() => detail.refetch()} />}
          {showWelcome && (
            <div className="mx-auto max-w-xl py-8 text-center">
              <ShieldCheck className="mx-auto size-8 text-primary" aria-hidden />
              <h1 className="mt-2 text-xl font-semibold">Ask about IOMETE</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Answers quote the official documentation or approved expert answers. If something can't be verified, I'll say so and raise it with the product team instead of guessing.
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {suggested.data?.questions.map((q) => (
                  <button key={q} type="button" onClick={() => submit(q)} className="rounded-full border bg-card px-3 py-1.5 text-sm hover:border-primary hover:text-primary">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => (m.role === "USER" ? <UserBubble key={m.id} text={m.content} /> : <AssistantMessage key={m.id} m={m} liveStatus={m.ticket ? liveStatus.get(m.ticket.id) : undefined} onOpenAssessment={() => navigate("/buyer")} />))}
          {pending && (
            <>
              <UserBubble text={pending} />
              <div className="max-w-2xl space-y-2 rounded-lg border bg-slate-50 p-4" aria-busy="true">
                <p className="text-sm text-muted-foreground">Searching product knowledge and checking evidence…</p>
                <Skeleton className="h-3 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </>
          )}
          {failed && (
            <div className="max-w-2xl">
              <ErrorState error={failed.error} title="The answer could not be produced" onRetry={() => submit(failed.question)} />
            </div>
          )}
          <div ref={bottomRef} />
        </div>
        <div className="border-t p-3">
          <label htmlFor="chat-input" className="sr-only">
            Your question
          </label>
          <div className="flex items-end gap-2">
            <Textarea
              id="chat-input"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKey}
              maxLength={MAX}
              rows={2}
              placeholder="Ask a question about IOMETE… (Enter to send, Shift+Enter for a new line)"
              className="resize-none"
            />
            <Button onClick={() => submit(draft)} disabled={!draft.trim() || send.isPending} aria-label="Send question">
              <Send aria-hidden />
            </Button>
          </div>
          <div className="mt-1 flex justify-between gap-2 text-xs text-muted-foreground">
            <span>{PRIVACY}</span>
            <span className="shrink-0 tabular-nums">
              {draft.length}/{MAX}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <p className="max-w-[80%] whitespace-pre-wrap rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">{text}</p>
    </div>
  );
}

function AssistantMessage({ m, liveStatus, onOpenAssessment }: { m: ChatMessage; liveStatus?: TicketStatus; onOpenAssessment: () => void }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const [openSources, setOpenSources] = useState<string>("");
  const [highlight, setHighlight] = useState<number | null>(null);
  const raise = useMutation({
    mutationFn: () => fetchRaise(m.id),
    onSuccess: (msg) => {
      toast.success(`Raised with the product team: ${msg.ticket?.display_id}`);
      qc.invalidateQueries({ queryKey: ["chat-session", userKey] });
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const cite = (n: number) => {
    setOpenSources("sources");
    setHighlight(n);
    window.setTimeout(() => document.getElementById(`cite-${m.id}-${n}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 120);
  };
  return (
    <article className="max-w-3xl space-y-3 rounded-lg border bg-slate-50/60 p-4">
      <AnswerTypeBadge type={m.answer_type} />
      <div className="text-sm text-slate-900">
        <Markdown text={m.content} onCite={m.citations.length ? cite : undefined} />
      </div>
      {m.general_explanation_markdown && m.answer_type !== "GENERAL_EXPLANATION" && (
        <div className="rounded-md border border-slate-200 bg-card p-3">
          <div className="mb-1 flex items-center gap-2">
            <SourceChip kind="general" />
            <span className="text-xs font-semibold text-slate-700">General explanation (not specific to IOMETE)</span>
          </div>
          <Markdown text={m.general_explanation_markdown} />
        </div>
      )}
      {m.answer_type === "PARTIAL" && m.unverified_aspects.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm">
          <p className="font-semibold text-amber-900">Not verified</p>
          <ul className="mt-1 list-disc pl-5 text-amber-900">
            {m.unverified_aspects.map((u) => (
              <li key={u}>{u}</li>
            ))}
          </ul>
          {!m.ticket && (
            <Button size="sm" variant="outline" className="mt-2" onClick={() => raise.mutate()} disabled={raise.isPending}>
              Ask the product team about the unverified part
            </Button>
          )}
        </div>
      )}
      {m.conflict_note && <p className="rounded-md border border-blue-200 bg-blue-50 p-2 text-sm text-blue-900">Sources disagree: {m.conflict_note}</p>}
      {m.ticket && (
        <div className="flex flex-wrap items-center gap-2 rounded-md border bg-card p-3 text-sm">
          <TicketIcon className="size-4 text-slate-500" aria-hidden />
          <span>
            Product team reference <strong>{m.ticket.display_id}</strong>
          </span>
          <TicketStatusBadge status={liveStatus ?? m.ticket.status} />
          <Link to="/chat/questions" className="ml-auto text-xs font-medium text-primary hover:underline">
            View in My questions
          </Link>
        </div>
      )}
      {m.action?.type === "OPEN_ASSESSMENT" && (
        <Button size="sm" onClick={onOpenAssessment}>
          Capture it in an assessment <ArrowRight aria-hidden />
        </Button>
      )}
      {m.citations.length > 0 && (
        <Accordion type="single" collapsible value={openSources} onValueChange={setOpenSources}>
          <AccordionItem value="sources" className="border-b-0">
            <AccordionTrigger>Sources ({m.citations.length})</AccordionTrigger>
            <AccordionContent className="space-y-2">
              {m.citations.map((c) => (
                <EvidenceCard key={c.n} c={c} id={`cite-${m.id}-${c.n}`} highlight={highlight === c.n} />
              ))}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}
    </article>
  );
}

function fetchRaise(id: string) {
  return chatApi.raiseTicket(id);
}
