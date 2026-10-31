import { ArrowRight, BookOpenCheck, CheckCircle2, ClipboardList, Handshake, HelpCircle, MessageCircleQuestion, ShieldCheck, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const STEPS = [
  { icon: ClipboardList, title: "Describe your needs", text: "Upload a requirements PDF, chat about what you need, or fill in a guided form." },
  { icon: BookOpenCheck, title: "See evidence-backed fit", text: "Each requirement gets one status, with excerpts quoted from official documentation." },
  { icon: Handshake, title: "Share with the seller", text: "You decide what to share. The seller responds to gaps and follow-ups." },
  { icon: Sparkles, title: "Questions become knowledge", text: "Questions the product docs cannot answer go to experts. Approved answers become reusable." },
];

export function LandingPage() {
  return (
    <div className="space-y-12">
      <section className="pt-6 text-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-primary">Evaluate IOMETE with evidence</p>
        <h1 className="mx-auto mt-2 max-w-3xl text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
          Turn your requirements and product questions into cited answers and clear next steps
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
          DealBridge checks your requirements against official product documentation and approved expert answers. It shows what is supported, what is
          not established, and what to ask next. Every claim links to its source.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="flex flex-col">
          <CardHeader>
            <ClipboardList className="size-6 text-primary" aria-hidden />
            <CardTitle className="text-lg">Assess your requirements</CardTitle>
            <CardDescription>Capture what you need and get a requirement-by-requirement assessment with evidence, gaps and questions for the seller.</CardDescription>
          </CardHeader>
          <CardContent className="mt-auto">
            <Button asChild>
              <Link to="/buyer">
                Start an assessment <ArrowRight aria-hidden />
              </Link>
            </Button>
          </CardContent>
        </Card>
        <Card className="flex flex-col">
          <CardHeader>
            <MessageCircleQuestion className="size-6 text-primary" aria-hidden />
            <CardTitle className="text-lg">Ask about the product</CardTitle>
            <CardDescription>Ask natural-language questions. Answers cite the documentation, and questions it cannot verify go to the product team.</CardDescription>
          </CardHeader>
          <CardContent className="mt-auto">
            <Button asChild variant="outline">
              <Link to="/chat">
                Open product chat <ArrowRight aria-hidden />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </section>

      <section aria-labelledby="how">
        <h2 id="how" className="text-xl font-semibold">How it works</h2>
        <ol className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <li key={s.title} className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <span className="flex size-6 items-center justify-center rounded-full bg-accent text-xs text-accent-foreground">{i + 1}</span>
                <s.icon className="size-4 text-primary" aria-hidden />
                {s.title}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="not" className="rounded-lg border bg-card p-6">
        <h2 id="not" className="flex items-center gap-2 text-xl font-semibold">
          <ShieldCheck className="size-5 text-primary" aria-hidden /> What DealBridge does not do
        </h2>
        <ul className="mt-4 space-y-3 text-sm">
          <li className="flex gap-2">
            <HelpCircle className="mt-0.5 size-4 shrink-0 text-slate-500" aria-hidden />
            <span><strong>It is not a guarantee.</strong> Results are a preliminary, evidence-based assessment, not a contract or a certification.</span>
          </li>
          <li className="flex gap-2">
            <HelpCircle className="mt-0.5 size-4 shrink-0 text-slate-500" aria-hidden />
            <span><strong>Unknown stays unknown.</strong> If the documentation does not establish something, DealBridge says so instead of guessing.</span>
          </li>
          <li className="flex gap-2">
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-slate-500" aria-hidden />
            <span><strong>People still validate.</strong> Your environment's specifics need confirmation from the vendor and your own testing.</span>
          </li>
        </ul>
      </section>
    </div>
  );
}
