# Decisions

One line per decision: **decision**. Reason.

## Owner overrides (take precedence over the build prompt)
- **Repository root is `hackCbs9/`.** Requested by the project owner.
- **LLM provider is Qwen (Alibaba Cloud Model Studio / DashScope), not Anthropic.** Owner instruction; replaces build-prompt §3/§13 "Anthropic only". Accessed through the official `openai` Python SDK against DashScope's OpenAI-compatible endpoint (`LLM_BASE_URL`, default `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`). No other provider, no LangChain/LlamaIndex.
- **`LLM_MODEL=qwen3.8-max`, `LLM_FAST_MODEL=qwen3.8-flash`.** Newest Max and Flash model codes listed on https://www.alibabacloud.com/help/en/model-studio/models (fetched 2026-10-31). Both are configurable.
- **Structured output via a forced function call (`tool_choice` naming the function) with `enable_thinking=false` passed in `extra_body`.** Third-party Qwen docs state that forced tool choice is unavailable in thinking mode. If the API rejects forcing, fall back to `response_format={"type":"json_object"}` with the JSON schema in the prompt; both paths validate with Pydantic.
- **`LLM_PROVIDER` accepts only `qwen`.** Single-provider rule kept, with the provider swapped.
- **No Claude/AI co-author trailers in commits.** Owner instruction; commits use the owner's git identity.
- **Deployment target: GitHub plus Vercel.** Owner instruction. Vercel hosts the static frontend. The backend (FastAPI, PostgreSQL, Qdrant, local embedding model) cannot run on Vercel serverless and needs separate hosting, decided at deploy time.

## Environment
- **Container runtime: Colima (`brew install colima docker docker-compose`).** Docker Desktop was not installed; owner chose Colima.
- **Python 3.12 from Homebrew (`/opt/homebrew/bin/python3.12`).** System python3 is 3.9.6, below the 3.11 minimum.

## Knowledge format
- **OKF specification found and followed: Open Knowledge Format v0.2, GoogleCloudPlatform/open-knowledge-format `SPEC.md` at commit ad30107c31c06aec8a7d5636e0d1058118604e6f.** DMKB fallback not used.
- **No official OKF validator exists in the spec repo (it ships a reference agent, not a validator), so `scripts/ingest_okf.py --validate-only` implements the spec's §11 conformance rules exactly, plus DealBridge's stricter project rules.** Third-party validators (Rust okf-validator, Go skosovsky/okf, Python okf-schema) are unofficial; adding Rust or Go toolchains is not justified.
- **Bundle navigation file is `index.md` (OKF reserved name), not `INDEX.md`.** OKF §3.1 reserves `index.md`, and macOS filesystems are case-insensitive, so the two names would collide.
- **`README.md` and `OKF_CONFORMANCE.md` live in `knowledge/official/`, outside the bundle root `knowledge/official/iomete/`.** OKF §3.1 treats every non-reserved `.md` in the bundle as a concept requiring a `type` frontmatter key; navigation files inside the bundle would break conformance.
- **Build-prompt metadata is carried as OKF producer extension keys (`knowledge_id`, `category`, `source_type`, `source_url`, `source_document`, `last_verified_at`, `version`, `approval_status`) alongside OKF-native keys (`type`, `title`, `description`, `resource`, `tags`, `status`, `generated`, `verified`, `sources`).** OKF §4.1 allows extensions; the mapping is documented in OKF_CONFORMANCE.md.
- **`approval_status: approved` requires OKF `status: stable`; `draft` requires `status: draft`.** Keeps the two lifecycle fields consistent; the validator enforces it.
- **`verified.by` is `process:dealbridge-excerpt-check`, recorded only after the excerpt checker confirms every quoted excerpt verbatim against the live source page.** Honest trust tier ("machine-confirmed"). No human has reviewed the content, so no `human:` actor is claimed.
- **IOMETE docs are fetched from `https://iomete.com/resources/...` (Docusaurus).** Located via robots.txt, then sitemap.xml.
- **The hackathon starter kit PDF was used only for links, not as a fact source (R8).** Its IOMETE claims are marketing summaries, not documentation pages.
- **PostgreSQL container is published on host port 5433 (`POSTGRES_HOST_PORT`), not 5432.** A pre-existing PostgreSQL server on the development machine already listens on 5432; DealBridge does not touch it.

## Retrieval calibration (G2, `scripts/calibrate_threshold.py`, 37 answerable / 17 unanswerable questions, official collection, top 6)
| threshold | recall@6 | false-accept rate |
|---|---|---|
| 0.30 | 100% | 100% |
| 0.35 | 100% | 100% |
| 0.40 | 100% | 100% |
| 0.45 | 100% | 88% |
| 0.50 | 100% | 82% |
| 0.55 | 100% | 71% |
| 0.60 | 97% | 47% |
| 0.65 | 70% | 24% |
| 0.70 | 49% | 6% |
| 0.75 | 30% | 0% |
| 0.80 | 11% | 0% |

- **`RETRIEVAL_MIN_SCORE=0.60`.** No threshold reaches recall ≥ 90% with false-accept ≤ 10%, so this is the best trade-off, stated explicitly: recall 97%, false-accept 47%. Off-topic questions top out at 0.40–0.47 and are removed. On-topic but undocumented questions (MFA 0.71, HSM keys 0.69, SOC 2 0.67, HIPAA 0.66) cannot be separated by similarity at all. They are handled downstream by verbatim quote verification, the explicit-certification rule and the faithfulness check, which is why similarity is never treated as evidence (R3).
- **`RESOLVED_REUSE_MIN_SCORE=0.70`.** On 3 synthetic stored Q&A records with 9 paraphrases and 9 non-matching questions, paraphrase scores ranged 0.633–0.80+ and non-matching scores reached up to 0.783 (the distributions overlap). At 0.70, 8/9 paraphrases and 3/9 non-matching questions are flagged as reuse candidates. 0.80 would reuse only 1/9 paraphrases. A flagged answer is only *preferred*: the answer prompt (rule c) must still reject it on any version, environment or customer-condition mismatch, and every claim must quote it verbatim.
- **`TICKET_DUP_MIN_SCORE=0.85` kept.** Measured document-to-document similarities: close paraphrases 0.96–0.97, "Kubernetes 1.30 vs 1.24" 0.953, "encrypted at rest vs in transit" 0.872, "SOC 2 vs ISO 27001" 0.757. Qualifier differences can exceed the threshold, so the LLM same-intent and differing-qualifier check is mandatory before linking.

## Implementation choices (G0–G7)
- **Tailwind CSS v4 (CSS-first `@theme` tokens) with a minimal `tailwind.config.ts` loaded via `@config`.** v4 is the current stable release; shadcn/ui supports it.
- **shadcn/ui components were written into `src/components/ui/` by hand (new-york style) instead of via the CLI.** Same code; avoids network fetches from the registry.
- **TypeScript 6: `baseUrl` removed (deprecated); `paths` alone resolves `@/*`.**
- **The Qdrant client is created with `check_compatibility=False`.** Client and server are both 1.20.0; this avoids a version probe on every connection.
- **rapidfuzz comparisons use `processor=utils.default_process`.** rapidfuzz 3 no longer strips punctuation by default, and without it near-identical texts scored below 92.
- **Global knowledge stores a *redacted* `question_original`.** Build prompt §8.5 lists `question_original` in the payload, but R6 and §14 forbid buyer data in global knowledge, so R6 wins. The raw text stays only on the internal ticket.
- **`evidence_references.role` (SUPPORTS | LIMITS | RELATED) was added** to support the required rank order and UI labels.
- **The answer endpoint for tickets uses an explicit `/request-revision` route** (the §9.5 table lists the transition; §11.2 omits the path).
- **Every chat proposal requires an explicit Apply.** This satisfies the "ask when ambiguous or materially different" rule without heuristics. UPDATE and REMOVE ops whose target id is unknown are dropped before display.
- **The buyer's report includes their unresolved tickets; the seller's copy omits that section.** Sellers never see tickets (R6).
- **Seller responses made on earlier versions are shown on later versions with their version number.** They are attributed and never change statuses.
- **Integration tests run against `dealbridge_test` and `test_`-prefixed Qdrant collections**, created and dropped by fixtures. Development data is never touched.
- **Frontend dev convenience: `?demo_user=<id>` selects an identity in development builds only (`import.meta.env.DEV`).** Used for headless screenshots; stripped from production builds.
- **Real-LLM tests are excluded from `make test` (`-m "not llm"`) and run with `make test-llm`.**
