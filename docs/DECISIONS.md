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
