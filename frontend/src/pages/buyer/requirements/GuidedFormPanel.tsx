import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUserKey } from "@/hooks/useIdentity";
import { assessmentsApi } from "@/services/assessments";
import { type Assessment, PRIORITY_LABELS, type Priority } from "@/types/api";

const PRIORITIES = Object.keys(PRIORITY_LABELS) as Priority[];
const text = z.string().max(4000, "4,000 characters max").optional();
const schema = z.object({
  organisation_name: z.string().max(200).optional(),
  industry: z.string().max(200).optional(),
  use_case: z.string().trim().min(1, "Intended use case is required").max(4000),
  deployment_preference: z.string(),
  data_sovereignty: text,
  data_scale: z.string().max(500).optional(),
  existing_technologies: text,
  security_access: text,
  compliance: text,
  performance_availability: text,
  budget_operations: text,
  other: text,
  priorities: z.record(z.string(), z.string()),
});
type Form = z.infer<typeof schema>;

type Field = { key: keyof Form; label: string; kind: "text" | "textarea" | "deployment"; optional?: boolean; producesReqs?: boolean };
const SECTIONS: { title: string; fields: Field[] }[] = [
  { title: "About you", fields: [ { key: "organisation_name", label: "Organisation", kind: "text", optional: true }, { key: "industry", label: "Industry", kind: "text", optional: true } ] },
  { title: "Use and deployment", fields: [
    { key: "use_case", label: "Intended use case", kind: "textarea", producesReqs: true },
    { key: "deployment_preference", label: "Deployment preference", kind: "deployment", producesReqs: true },
    { key: "data_sovereignty", label: "Data sovereignty and residency", kind: "textarea", producesReqs: true },
    { key: "data_scale", label: "Data volume or scale", kind: "text", optional: true, producesReqs: true },
  ] },
  { title: "Technology, security and compliance", fields: [
    { key: "existing_technologies", label: "Existing data technologies and integrations", kind: "textarea", producesReqs: true },
    { key: "security_access", label: "Security and access-control needs", kind: "textarea", producesReqs: true },
    { key: "compliance", label: "Compliance or certification requirements", kind: "textarea", producesReqs: true },
    { key: "performance_availability", label: "Performance and availability expectations", kind: "textarea", producesReqs: true },
  ] },
  { title: "Other", fields: [
    { key: "budget_operations", label: "Budget or operational constraints", kind: "textarea", optional: true, producesReqs: true },
    { key: "other", label: "Other requirements", kind: "textarea", producesReqs: true },
  ] },
];
const DEPLOYMENT = [
  ["UNDECIDED", "Undecided"], ["ON_PREMISES", "On-premises"], ["OWN_CLOUD", "Own cloud account"], ["HYBRID", "Hybrid"], ["AIR_GAPPED", "Air-gapped"], ["PUBLIC_CLOUD", "Public cloud"],
];

export function GuidedFormPanel({ assessment }: { assessment: Assessment }) {
  const userKey = useUserKey();
  const qc = useQueryClient();
  const prev = (assessment.intake_form ?? {}) as Record<string, unknown>;
  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      organisation_name: (prev.organisation_name as string) ?? assessment.context.organisation_name ?? "",
      industry: (prev.industry as string) ?? assessment.context.industry ?? "",
      use_case: (prev.use_case as string) ?? assessment.context.use_case ?? "",
      deployment_preference: (prev.deployment_preference as string) ?? "UNDECIDED",
      data_sovereignty: (prev.data_sovereignty as string) ?? "",
      data_scale: (prev.data_scale as string) ?? "",
      existing_technologies: (prev.existing_technologies as string) ?? "",
      security_access: (prev.security_access as string) ?? "",
      compliance: (prev.compliance as string) ?? "",
      performance_availability: (prev.performance_availability as string) ?? "",
      budget_operations: (prev.budget_operations as string) ?? "",
      other: (prev.other as string) ?? "",
      priorities: (prev.priorities as Record<string, string>) ?? {},
    },
  });
  const submit = useMutation({
    mutationFn: (v: Form) => assessmentsApi.submitForm(assessment.id, v),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["requirements", userKey, assessment.id] });
      qc.invalidateQueries({ queryKey: ["assessment", userKey, assessment.id] });
      toast.success(r.changed_fields.length ? `${r.created} requirements created; please review and confirm them below.` : "No fields changed.");
    },
    onError: (e: Error) => toast.error(e.message),
  });
  const errors = form.formState.errors;
  return (
    <form className="space-y-6" onSubmit={form.handleSubmit((v) => submit.mutate(v))} noValidate>
      <p className="text-sm text-muted-foreground">A discovery aid, not an exhaustive checklist. Each answered field becomes one or more unconfirmed requirements you can review below. Resubmitting only re-processes fields you changed.</p>
      {SECTIONS.map((sec) => (
        <fieldset key={sec.title} className="space-y-3">
          <legend className="mb-1 text-sm font-semibold">{sec.title}</legend>
          {sec.fields.map((f) => (
            <div key={f.key} className="grid gap-2 md:grid-cols-[1fr_11rem]">
              <div className="space-y-1.5">
                <Label htmlFor={`f-${f.key}`}>{f.label}{f.key === "use_case" ? " (required)" : f.optional ? " (optional)" : ""}</Label>
                {f.kind === "text" && <Input id={`f-${f.key}`} {...form.register(f.key as "industry")} />}
                {f.kind === "textarea" && <Textarea id={`f-${f.key}`} rows={2} {...form.register(f.key as "other")} />}
                {f.kind === "deployment" && (
                  <Controller control={form.control} name="deployment_preference" render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id={`f-${f.key}`}><SelectValue /></SelectTrigger>
                      <SelectContent>{DEPLOYMENT.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent>
                    </Select>
                  )} />
                )}
                {errors[f.key] && <p className="text-xs text-red-700">{String(errors[f.key]?.message)}</p>}
              </div>
              {f.producesReqs && (
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground" htmlFor={`p-${f.key}`}>Priority</Label>
                  <Controller control={form.control} name="priorities" render={({ field }) => (
                    <Select value={field.value[f.key] ?? "NOT_SPECIFIED"} onValueChange={(v) => field.onChange({ ...field.value, [f.key]: v })}>
                      <SelectTrigger id={`p-${f.key}`} aria-label={`${f.label} priority`}><SelectValue /></SelectTrigger>
                      <SelectContent>{PRIORITIES.map((p) => <SelectItem key={p} value={p}>{PRIORITY_LABELS[p]}</SelectItem>)}</SelectContent>
                    </Select>
                  )} />
                </div>
              )}
            </div>
          ))}
        </fieldset>
      ))}
      <Button type="submit" disabled={submit.isPending}>{submit.isPending ? "Processing…" : "Create requirements from form"}</Button>
    </form>
  );
}
