# Implementation plan (one page)

**Stack (pinned 2026-10-31):**
- Backend: Python 3.12, FastAPI 0.162.0, Pydantic 2.14.2, SQLAlchemy 2.1.6, Alembic 1.20.1, psycopg 3.3.6, qdrant-client 1.20.0, fastembed 0.9.1 (BAAI/bge-small-en-v1.5, 384d), openai SDK 3.42.0 (OpenRouter OpenAI-compatible API), PyMuPDF 2.0, ReportLab 5.1.0. Full pins in `backend/requirements.txt` plus the transitive lock.
- Frontend: React 18, TypeScript 6 (strict), Vite, React Router, TanStack Query, react-hook-form + zod, Tailwind v4, shadcn/ui (Radix), lucide-react, sonner, react-markdown + remark-gfm, self-hosted Inter. Pinned by `frontend/package-lock.json`.
- Infra: Docker Compose on Colima. `postgres:16-alpine` on host port 5433; `qdrant/qdrant:v1.20.0` on ports 6333 and 6334.

**LLM:** OpenRouter (owner override of the Anthropic default), using `openai/gpt-4.1` for main and fast tasks via the OpenAI-compatible API. Structured output uses forced function calling with Pydantic validation. Tests use a scripted FakeLLM.

**OKF outcome:** the spec was found. OKF v0.2 (GoogleCloudPlatform/open-knowledge-format@ad30107) is followed exactly. The bundle root is `knowledge/official/iomete/`, with `index.md` and `log.md` reserved, and each concept carries `type`. DealBridge metadata is carried as OKF extension keys. There is no official validator, so §11 conformance is implemented in `scripts/ingest_okf.py --validate-only`.

**IOMETE pages to curate** (53 fetched; see `docs/knowledge-sources.md`):
- Getting started: what-is-iomete, architecture, scalability, platform tour.
- Deployment: deployment architecture, on-prem install, Kubernetes, multi-cluster, network policies, backend databases, truststore, ingress, life-cycle management.
- Security: security overview, LDAP, data-security overview, access policies (database, table and column), masking, row-level filters, tag-based policies, domain authorization (RAS), access tokens.
- Platform: SQL editor, Jupyter, Spark jobs, job orchestrator, streaming, compute clusters, data catalog, monitoring, Spark catalogs, table maintenance, storage configs.
- Integrations: overview, Airflow, dbt, Tableau, Power BI, Superset, Metabase, DBeaver, Git, query federation, JDBC sync.
- Iceberg: getting started, time travel.

Known gaps (`docs/KNOWLEDGE_GAPS.md`): no fetched documentation page addresses air-gapped deployment or names any compliance certification.

**Gate schedule:** strictly in order, each ending with tests, a PROGRESS.md entry and a commit.
- G0: foundations.
- G1: OKF bundle and ingestion.
- G2: grounded chatbot and calibration.
- G3: ticket and knowledge loop.
- G4: requirement intake.
- G5: assessment engine and versions.
- G6: report, sharing and seller.
- G7: polish, docs, demo run and final report.
- G8: P1 items, only after G7.

Real-LLM checks run once the owner adds `LLM_API_KEY` to `.env`.
