# DealBridge — Agent-Ready Product Requirements

**Document type:** Product and implementation requirements  
**Version:** 1.0  
**Project:** Hackathon MVP  
**Target build window:** Approximately 12 hours  
**Primary product context:** IOMETE track  
**Status:** Approved product direction; implementation details may be adapted to the existing repository

---

## 1. Product overview

DealBridge is an enterprise product-evaluation and buyer-seller collaboration platform. It helps a potential buyer express their technical and business requirements, understand how a product maps to those requirements, identify missing evidence, and coordinate follow-up with the seller.

The system has two primary parts:

1. **Requirement Intelligence Engine** — a buyer and seller workflow for collecting, structuring, assessing, modifying, sharing and resolving buyer requirements.
2. **Dynamic Product Knowledge Engine** — a RAG-based product Q&A system that searches authoritative product knowledge and approved resolved queries. When it cannot answer reliably, it creates a ticket for an authorised human to resolve. Approved resolutions are added to the searchable knowledge base.

The two parts must share product knowledge, document ingestion utilities, evidence references and deal records. They are separate user experiences and workflows, not two unrelated applications.

### 1.1 Core value proposition

DealBridge transforms unstructured buyer requirements and product questions into evidence-backed assessments and actionable follow-up workflows.

It is not merely a generic chatbot or a PDF question-answering tool. Its value is the complete workflow:

**Understand requirements → retrieve product evidence → assess fit and gaps → coordinate follow-up → resolve unanswered questions → improve reusable knowledge.**

### 1.2 Product principles

- Evidence before claims: never invent product capabilities, certifications, integrations, security guarantees or compatibility.
- Unknown is a valid result: insufficient evidence must be shown as unknown or requiring validation.
- Human approval for new knowledge: developer/expert answers must be reviewed before becoming reusable knowledge.
- Separate source authority: official product documentation and approved resolved-query knowledge must remain distinguishable.
- Buyer privacy: one buyer must never see another buyer's private requirements, documents or conversations.
- Traceability: important assessments and answers must link to their sources.
- Editable requirements: buyers can correct extracted requirements and rerun the assessment.
- Practical MVP: build the complete critical path before adding optional polish.

---

## 2. Scope and priorities

### 2.1 P0 — must work in the hackathon MVP

1. Buyer can create an assessment.
2. Buyer can provide requirements through chat and/or a guided form.
3. Buyer can upload a PDF of requirements.
4. System extracts structured requirements and allows editing.
5. System assesses requirements against the official product knowledge base.
6. Each assessment has a supported status and evidence references.
7. Buyer can change requirements and trigger reassessment.
8. Buyer can download an assessment report as PDF.
9. Product knowledge chatbot performs semantic retrieval and gives grounded answers with citations.
10. Unanswered or weakly supported questions create tickets.
11. Admin/developer can review a ticket, submit a resolution and approve it.
12. Approved resolved answers are embedded and added to the resolved-query vector collection.
13. Future questions can retrieve approved resolved-query knowledge.
14. Basic seller view can inspect a buyer-shared assessment and its gaps.

### 2.2 P1 — implement if time permits

- Seller uploads product documentation.
- Seller can respond to individual requirements.
- Buyer can request a follow-up.
- Seller can accept, reject or respond to a follow-up request.
- Duplicate unresolved query detection.
- Excel export in addition to PDF.
- Rich assessment history and version comparison.
- Better dashboard metrics and filtering.

### 2.3 P2 — future roadmap

- Full authentication, organisation membership and granular RBAC.
- Real-time buyer-seller messaging.
- Email notifications.
- CRM integrations.
- Advanced analytics and query trend dashboards.
- Scheduled crawling and automatic change detection of official docs.
- Multi-product/vendor support.
- Human-in-the-loop review queues with SLAs.
- Production-grade tenant isolation, audit and retention policies.

Do not let P1/P2 work delay P0.

---

## 3. User roles

### 3.1 Buyer

A prospective customer evaluating a product.

Can:
- Create an assessment.
- Upload a PDF of requirements.
- Enter requirements through chat.
- Fill a guided requirement form.
- Review and edit extracted requirements.
- Run and rerun product-fit assessments.
- Ask general product questions in the Product Knowledge Chatbot.
- View evidence and unresolved gaps.
- Download a PDF assessment report.
- Explicitly share an assessment with the seller.
- Request follow-up from the seller.
- Provide additional information requested by the seller.

Cannot:
- Approve official product knowledge.
- Approve resolved-query knowledge.
- View another buyer's private data.
- Change seller-owned product claims.

### 3.2 Seller

A vendor representative or product sales/solutions team member.

Can:
- View assessments explicitly shared by a buyer.
- Upload product documents where enabled.
- Review structured buyer requirements.
- Review evidence, gaps and unknowns.
- Add a response or clarification to a requirement.
- Assign an internal owner to a follow-up task in the MVP if task ownership is implemented.
- Respond to buyer follow-up requests.
- Download the buyer assessment.

Cannot:
- Silently modify the buyer's original requirements.
- Mark a requirement as supported without evidence or an explicit, attributable human response.
- View assessments that have not been shared with them.

### 3.3 Admin / Developer / Product Expert

An authorised internal role responsible for resolving unanswered product questions.

Can:
- View the unresolved-query ticket queue.
- Inspect the original question, retrieval results and context.
- Submit a proposed answer.
- Attach supporting sources or internal notes.
- Approve, reject or request revision of a proposed answer.
- Publish an approved answer into resolved-query knowledge.
- Mark a knowledge entry as outdated or superseded.

For the hackathon, this role can be represented by a simple admin page or role switcher. Do not build complex authentication unless already available.

---

## 4. Part 1 — Requirement Intelligence Engine

### 4.1 Buyer requirement input

The buyer must have three ways to express needs.

#### A. PDF upload

- Accept PDF files.
- Validate file type and reasonable file-size limits.
- Extract text from the PDF.
- Detect likely requirement statements.
- Preserve the original source text and page number where available.
- If the PDF is scanned and text extraction is empty or poor, show a clear unsupported/scanned-document message. OCR is optional for the hackathon.
- Show extracted requirements for buyer review before final assessment.

#### B. Chat input

The buyer can describe their needs conversationally, for example:

> We need a self-hosted analytics platform. Our data cannot leave our infrastructure. We use Spark-based processing and need granular access controls.

The system should:
- Ask clarifying questions when a requirement is ambiguous.
- Extract multiple requirements from one message.
- Preserve constraints and qualifiers.
- Avoid turning assumptions into confirmed requirements.
- Let the buyer confirm the extracted structured requirements.

#### C. Guided form

Provide a form that captures, at minimum:

- Organisation and industry (optional).
- Intended use case.
- Deployment preference: on-premises, own cloud, hybrid, air-gapped, public cloud, undecided.
- Data sovereignty / data residency constraints.
- Data volume or scale (optional).
- Existing data technologies and integrations.
- Security and access-control needs.
- Compliance or certification requirements.
- Performance and availability expectations.
- Budget or operational constraints (optional).
- Other requirements.

The form is a discovery aid, not a fixed exhaustive schema. Allow free-text additions.

### 4.2 Requirement data model

Every extracted requirement should have:

- Stable requirement ID.
- Original requirement text.
- Normalised/clarified requirement text.
- Category.
- Priority/criticality.
- Source type: PDF, chat or form.
- Source reference: file/page/message/form field when available.
- Buyer-confirmed flag.
- Created and updated timestamps.
- Version or assessment association.

Suggested categories:
- Functional capability
- Deployment and infrastructure
- Data sovereignty and residency
- Security and access control
- Integration and compatibility
- Performance and scalability
- Availability and reliability
- Compliance and governance
- Cost and operations
- Other

Priority labels:
- Critical
- High
- Medium
- Low
- Not specified

Do not infer a legal or compliance requirement from vague wording. Ask the buyer to clarify.

### 4.3 Requirement confirmation and editing

After extraction:
- Display requirements in a structured table or cards.
- Allow buyer to edit, delete or add requirements.
- Preserve original extracted text for traceability.
- Require buyer confirmation before treating extracted requirements as the final assessment input.
- Any edit must mark the assessment as stale until reassessed.
- Reassessment must use the latest confirmed requirement set.
- Show which requirements changed since the previous assessment.

### 4.4 Product-fit assessment

For each requirement, retrieve evidence from official product knowledge and, where appropriate, approved resolved-query knowledge.

Each requirement must receive exactly one primary status:

| Status | Meaning |
|---|---|
| SUPPORTED | Reliable evidence directly supports the requirement |
| PARTIALLY_SUPPORTED | Evidence supports only part of the requirement or describes material limitations |
| NEEDS_VALIDATION | Related capability exists, but buyer-specific details or technical confirmation are needed |
| NOT_SUPPORTED | Reliable, current evidence indicates a mismatch |
| UNKNOWN | There is insufficient reliable evidence to reach a conclusion |

Rules:
- `SUPPORTED` requires one or more evidence references.
- `NOT_SUPPORTED` requires explicit, reliable evidence of the limitation. Absence of evidence is not proof of non-support.
- `PARTIALLY_SUPPORTED` must explain what is supported and what is not established.
- `NEEDS_VALIDATION` must state what information or test is required.
- `UNKNOWN` must explain what is missing.
- Every claim must show source name, source URL or internal reference, and relevant excerpt.
- Never present a similarity score as proof of capability.
- Never fabricate certifications, compliance status, integrations or product guarantees.
- If official and resolved-query sources conflict, flag the conflict and do not silently choose one.

Assessment output should include:
- Executive summary.
- Requirement-by-requirement status.
- Evidence and source excerpts.
- Assumptions.
- Missing information.
- Questions for the seller.
- Potential blockers.
- Recommended next steps.
- Assessment version and timestamp.

### 4.5 Dynamic requirement changes

Buyer can modify requirements at any time by:
- Editing a requirement directly.
- Adding/removing requirements.
- Sending a chat instruction such as “We no longer require air-gapped deployment, but we now require hybrid deployment.”

The system must:
1. Interpret the change.
2. Show the proposed changes.
3. Ask for confirmation if the change is ambiguous or materially alters meaning.
4. Update the structured requirement set.
5. Mark previous assessment as superseded/stale.
6. Reassess affected requirements. For the MVP, full reassessment is acceptable.
7. Generate a new assessment version.
8. Preserve previous versions for comparison.

Do not mutate the buyer's confirmed requirement history without traceability.

### 4.6 PDF report

Buyer can download a PDF containing:
- Deal/assessment title and date.
- Buyer-provided context.
- Executive summary.
- Requirements and their statuses.
- Evidence excerpts and source references.
- Assumptions and limitations.
- Unknowns and validation needs.
- Questions for the seller.
- Recommended next steps.
- Assessment version.

The report must clearly state that it is an evidence-based preliminary assessment, not a contractual guarantee or certification.

### 4.7 Buyer-seller follow-up

- Buyer must explicitly choose to share an assessment with a seller.
- Sharing should create a seller-visible assessment reference.
- Buyer can request a follow-up and optionally provide a message.
- Seller can view the shared assessment and respond.
- Seller response should be associated with the relevant assessment or requirement.
- Buyer can provide requested information.
- For the MVP, a simple follow-up request/response thread is sufficient. Real-time chat and notifications are optional.
- Show status: REQUESTED, IN_PROGRESS, RESPONDED, CLOSED.

### 4.8 Seller document upload

Seller may upload product documentation to support assessment responses.

For MVP:
- Accept PDF and text/Markdown documents if feasible.
- Associate uploaded documents with the seller/product.
- Treat seller-uploaded material as seller-provided evidence, not automatically as official knowledge.
- Show source provenance clearly.
- Do not silently merge seller uploads into the official OKF bundle.
- If seller content is intended to become official product knowledge, require an authorised review and publication process.

Seller dashboard should show:
- Shared buyer assessments.
- Buyer requirements.
- Assessment status and evidence.
- Unknown/validation items.
- Buyer questions and follow-up requests.
- Seller response controls.

---

## 5. Part 2 — Dynamic Product Knowledge Engine

### 5.1 Purpose

Provide an interactive chatbot, primarily for potential/new buyers, that answers questions about:
- Product capabilities.
- Deployment.
- Architecture.
- Security and access control.
- Tools and integrations.
- Product usage.
- General product concepts relevant to evaluating the product.

The chatbot must distinguish product-specific facts from general educational explanations.

### 5.2 Knowledge source architecture

Maintain two logically separate knowledge sources and two separate Qdrant collections.

#### Source A: Official product knowledge — OKF bundle

Use **Open Knowledge Format (OKF)** as the human-readable, version-controlled source of truth for curated official product knowledge.

Recommended repository structure (adapt to the actual OKF specification and validator used):

```text
knowledge/
└── official/
    └── iomete/
        ├── README.md
        ├── INDEX.md
        ├── deployment/
        ├── architecture/
        ├── security/
        ├── platform/
        └── integrations/
```

Important:
- Confirm the exact OKF specification and required bundle conventions before implementation.
- Do not invent an OKF schema. Follow the chosen OKF format's actual requirements.
- Markdown files should be human-readable and reviewable.
- Keep original source URLs and verification metadata.
- Track changes in Git.
- OKF is the source/organisation format, not the vector database.
- Parse the bundle, chunk content, generate embeddings and index it into Qdrant.
- Official knowledge should be curated from actual IOMETE documentation.
- Do not invent official IOMETE facts to populate missing sections.

Suggested metadata per knowledge item:
- `knowledge_id`
- `title`
- `category`
- `source_type = official`
- `source_url`
- `source_document`
- `last_verified_at`
- `version`
- `approval_status`
- `content_hash`

#### Source B: Resolved-query knowledge

Use **Qdrant** as the dedicated vector database for approved resolved-query knowledge.

Recommended collection:
- `resolved_query_knowledge`

Each record should contain:
- Original user question.
- Normalised question.
- Approved answer.
- Category/tags.
- Source/author.
- Reviewer/approver.
- Approval timestamp.
- Version.
- Validity/status.
- Embedding.
- Related ticket ID.
- Optional supporting references.

Resolved query knowledge is not automatically official documentation. It must remain labelled as an approved expert resolution.

### 5.3 Vector database recommendation

Use Qdrant, self-hosted locally via Docker for the hackathon.

Reasons:
- Open-source and self-hostable.
- Dedicated vector database service.
- Persistent storage.
- Metadata/payload filtering.
- API and Python client.
- Suitable for separate collections and future growth.

Official resources:
- https://qdrant.tech/documentation/
- https://github.com/qdrant/qdrant

Use two collections:
1. `official_product_knowledge`
2. `resolved_query_knowledge`

Keep application data (users, deals, requirements, assessments, tickets, tasks and conversations) in PostgreSQL. Do not use Qdrant as the transactional database.

### 5.4 Ingestion pipeline

For official OKF knowledge:
1. Read/validate the OKF bundle.
2. Discover supported knowledge files.
3. Parse metadata and content.
4. Normalise content.
5. Split content into meaningful chunks.
6. Generate embeddings.
7. Upsert vectors and metadata into `official_product_knowledge`.
8. Record bundle version and content hashes.
9. Remove or deactivate stale chunks when source content is deleted or changed.
10. Log ingestion outcome.

For resolved queries:
1. Ticket is resolved by an authorised expert.
2. Proposed answer is submitted.
3. Reviewer approves it.
4. Approved question and answer are normalised.
5. Generate embedding.
6. Upsert into `resolved_query_knowledge`.
7. Mark the ticket as published.
8. Make the new knowledge available to future searches.

Do not index pending, rejected or unapproved answers.

### 5.5 Query pipeline

For every incoming question:
1. Identify user/session and query context.
2. Classify the query: product-specific, general educational, requirement-assessment-related, or unsupported/out of scope.
3. Rewrite/normalise query if needed while preserving intent.
4. Generate query embedding.
5. Search both Qdrant collections.
6. Apply metadata filters and source-authority rules.
7. Evaluate relevance and whether the retrieved passages actually answer the question.
8. If evidence is sufficient, generate a grounded answer with citations.
9. If evidence is insufficient, explain that the answer is not currently verified and offer/create an unresolved-query ticket.
10. Store conversation and retrieval trace as appropriate.

Retrieval should return:
- Source collection.
- Knowledge item ID.
- Source title.
- Excerpt.
- URL or reference.
- Similarity/relevance score.
- Approval and validity metadata.

Do not expose raw internal metadata to users unless useful.

### 5.6 Retrieval and answer rules

- Semantic similarity is a retrieval signal, not proof of factual support.
- Use a configurable retrieval threshold, calibrated with test questions.
- Consider a second-stage relevance/grounding check.
- If no adequate evidence is found, do not guess.
- Cite the exact source chunks used.
- Prefer current official product knowledge for product claims.
- Approved resolved-query answers may supplement official docs, but must be labelled as expert-verified answers.
- If sources conflict, show that the information needs review.
- General educational answers must be labelled as general explanations and must not be represented as IOMETE capabilities.
- If the user asks about a certification or compliance status, require explicit evidence.
- Never claim that the system is fully hallucination-proof.

### 5.7 Unanswered query ticket lifecycle

Ticket creation:
- Create a ticket when retrieval is insufficient, conflicting or unsupported.
- Before creating a new ticket, search for semantically similar existing tickets and approved answers.
- If a similar open ticket exists, link the new query to it or increment its occurrence count.
- If a similar approved answer exists and remains valid, use it.
- Preserve the user's original question and relevant conversation context, subject to privacy rules.
- Do not put private buyer requirements into global reusable knowledge.

Suggested ticket fields:
- `ticket_id`
- `original_question`
- `normalised_question`
- `category`
- `conversation_id`
- `created_by`
- `status`
- `priority`
- `occurrence_count`
- `proposed_answer`
- `supporting_sources`
- `assigned_to`
- `reviewed_by`
- `created_at`
- `updated_at`
- `resolved_at`
- `published_knowledge_id`

Ticket statuses:
- OPEN
- IN_REVIEW
- ANSWER_PROPOSED
- APPROVED
- REJECTED
- PUBLISHED
- CLOSED

Admin workflow:
1. Admin opens ticket.
2. Reviews question and retrieval attempts.
3. Adds an answer and supporting evidence.
4. Submits for approval or approves if authorised.
5. On approval, system indexes the resolution.
6. Ticket becomes PUBLISHED.
7. Future matching queries can retrieve it.

For a one-person hackathon admin role, the same person may propose and approve, but the system data model should preserve both fields.

### 5.8 Dynamic vector database updates

The database must update incrementally:
- New approved answer: create embedding and upsert.
- Updated answer: create a new version and update/re-point the active record.
- Rejected answer: never index.
- Deleted/revoked answer: remove or deactivate its vector record.
- Superseded answer: retain history if appropriate, but exclude it from normal retrieval.
- Official OKF update: re-ingest changed files using content hashes; avoid duplicating unchanged chunks.

Do not rebuild the entire vector database for every new answer.

### 5.9 Duplicate detection

Use semantic similarity plus metadata and human review to identify:
- Repeated questions.
- Existing open tickets.
- Existing approved answers.

Do not merge questions solely because embeddings are similar. Preserve meaningful differences such as product version, deployment environment or customer-specific conditions.

---

## 6. Shared data and persistence architecture

Recommended services:

- **Frontend:** React + TypeScript.
- **Backend API:** Python FastAPI.
- **Transactional database:** PostgreSQL.
- **Vector database:** Qdrant.
- **Official knowledge source:** OKF bundle in the repository/Git.
- **File storage:** local storage for hackathon or Supabase Storage if already configured.
- **LLM:** use an available API provider configured through environment variables.
- **Embeddings:** use one consistent embedding model for indexing and querying.

Do not introduce multiple LLM providers or complex orchestration unless necessary.

### 6.1 Suggested relational entities

At minimum:

1. `users` — optional for MVP; can use demo identities.
2. `organizations`
3. `deals` or `assessments`
4. `uploaded_documents`
5. `requirements`
6. `assessment_versions`
7. `requirement_assessments`
8. `evidence_references`
9. `follow_up_requests`
10. `follow_up_messages`
11. `tickets`
12. `knowledge_records`
13. `conversations`
14. `messages`
15. `audit_events` — simplified for MVP.

Use UUID primary keys where practical.

Qdrant point IDs should be linked to relational `knowledge_records` or source IDs.

### 6.2 Assessment and evidence data

A requirement assessment should store:
- Requirement ID.
- Assessment version.
- Status.
- Explanation.
- Evidence references.
- Missing information.
- Assumptions.
- Confidence/relevance metadata if used.
- Assessed timestamp.
- Model/prompt version where practical.

Confidence is not a substitute for evidence.

### 6.3 Tenant and privacy boundaries

Even if full authentication is deferred:
- Every assessment must have an owner or demo buyer identity.
- Seller access must require explicit sharing.
- Global knowledge must not contain private buyer data.
- Conversation context must not leak between users.
- Ticket context must be minimised and sanitised before any reusable knowledge publication.

---

## 7. Suggested API surface

Exact route names can be adapted to the existing codebase.

### Assessment APIs

- `POST /api/assessments` — create assessment.
- `GET /api/assessments/{id}` — get assessment.
- `POST /api/assessments/{id}/documents` — upload PDF.
- `POST /api/assessments/{id}/requirements/extract` — extract requirements.
- `GET /api/assessments/{id}/requirements` — list requirements.
- `PATCH /api/requirements/{id}` — edit requirement.
- `POST /api/assessments/{id}/requirements` — add requirement.
- `POST /api/assessments/{id}/analyze` — run assessment.
- `GET /api/assessments/{id}/results` — get results.
- `GET /api/assessments/{id}/versions` — list versions.
- `GET /api/assessments/{id}/report.pdf` — download PDF.

### Buyer/seller APIs

- `POST /api/assessments/{id}/share` — explicitly share with seller.
- `GET /api/seller/assessments` — list shared assessments.
- `GET /api/seller/assessments/{id}` — view shared assessment.
- `POST /api/assessments/{id}/follow-ups` — buyer requests follow-up.
- `POST /api/follow-ups/{id}/responses` — seller responds.
- `POST /api/requirements/{id}/seller-response` — seller adds response/evidence.

### Product knowledge chatbot APIs

- `POST /api/chat/sessions` — create chat session.
- `POST /api/chat/sessions/{id}/messages` — send question.
- `GET /api/chat/sessions/{id}` — retrieve conversation.

### Ticket and knowledge APIs

- `GET /api/admin/tickets` — list tickets.
- `GET /api/admin/tickets/{id}` — ticket detail.
- `POST /api/admin/tickets/{id}/answer` — submit proposed answer.
- `POST /api/admin/tickets/{id}/approve` — approve and publish.
- `POST /api/admin/tickets/{id}/reject` — reject.
- `POST /api/admin/knowledge/reindex` — trigger controlled reindex.
- `GET /api/admin/knowledge/status` — ingestion/index status.

---

## 8. Frontend pages and UI requirements

### 8.1 Landing page

Explain the two core capabilities:
- Assess your requirements.
- Ask questions about the product.

Provide clear calls to action.

### 8.2 Buyer assessment flow

Pages/components:
- Create assessment.
- Upload PDF.
- Chat-based requirement input.
- Guided requirement form.
- Extracted requirement review.
- Assessment results.
- Requirement detail/evidence panel.
- Assessment history/version comparison.
- PDF export.
- Share with seller/follow-up request.

### 8.3 Product knowledge chatbot

Provide an interactive, welcoming interface for a first-time buyer:
- Suggested questions.
- Natural-language chat.
- Streaming or clear loading states if practical.
- Source citations with expandable excerpts.
- Clear indication when an answer is general versus product-specific.
- “I couldn't verify this” response with ticket creation option.
- Ticket reference/status after creation.
- Follow-up questions.
- Conversation history for the current user/session.

### 8.4 Seller workspace

- List buyer-shared assessments.
- Assessment overview.
- Requirement statuses.
- Evidence and unknowns.
- Respond to requirement.
- Follow-up queue.
- Seller document upload if implemented.

### 8.5 Admin/developer workspace

- Unresolved tickets.
- Ticket detail and retrieval trace.
- Proposed answer editor.
- Supporting evidence input.
- Approve/reject controls.
- Published knowledge list.
- Reindex status.

### 8.6 UI quality

- Use a consistent, polished SaaS design.
- Make evidence status visually clear.
- Avoid overloading the interface with raw technical metadata.
- Provide useful empty, loading, error and success states.
- Use realistic demo data.
- Do not display fake live metrics as real measurements.

---

## 9. Recommended technical implementation

### 9.1 Stack

Recommended default:
- React + TypeScript + Vite.
- Tailwind CSS and shadcn/ui.
- FastAPI.
- PostgreSQL.
- Qdrant.
- Python document parsing libraries.
- LLM API configured through environment variables.
- Embedding model configured through environment variables.
- PDF report generation using a Python PDF library.

If the repository already has a functioning stack, inspect it first and reuse it rather than replacing it.

### 9.2 Qdrant collections

Create:
- `official_product_knowledge`
- `resolved_query_knowledge`

Payload metadata should include:
- `knowledge_id`
- `title`
- `category`
- `source_type`
- `source_url`
- `source_document`
- `approval_status`
- `version`
- `content_hash`
- `updated_at`
- `validity_status`

Use metadata filters to restrict retrieval to approved and active entries.

### 9.3 Embedding model

Choose one embedding model and use the same model and vector dimension for both collections and query embeddings.

Prefer a free/local embedding model if machine resources permit. If using a hosted embedding API, configure it through environment variables and document any costs.

Never change embedding models without a reindex/migration plan.

### 9.4 OKF ingestion

- Treat the OKF bundle as the canonical editable source for official product knowledge.
- Confirm and follow the actual OKF specification selected by the team.
- Parse only supported content files.
- Preserve metadata and source references.
- Chunk by semantic sections/headings rather than arbitrary huge text blocks.
- Track hashes so unchanged files are not needlessly re-embedded.
- Make ingestion repeatable and idempotent.

### 9.5 Background processing

For hackathon scope, synchronous processing is acceptable for small files. If a workflow takes too long:
- Return a job ID.
- Track status in PostgreSQL.
- Expose a status endpoint.
- Show progress in the UI.

Do not add Celery/Redis unless needed by the actual implementation.

---

## 10. Security, privacy and reliability

Minimum requirements:
- Validate file type and size.
- Treat uploaded files as untrusted input.
- Do not execute content from uploaded documents.
- Keep API keys server-side.
- Use environment variables and provide `.env.example`.
- Do not commit secrets.
- Do not expose one buyer's assessment to another buyer.
- Require explicit buyer sharing before seller access.
- Keep private buyer data out of global resolved-query knowledge.
- Require human approval before publishing resolved knowledge.
- Store source provenance.
- Handle malformed PDFs, empty extraction, LLM errors and vector DB outages gracefully.
- Do not claim compliance certifications or security properties without evidence.

For a public deployment, authentication, authorisation, tenant isolation, rate limits and secure file storage become mandatory before real customer use.

---

## 11. Acceptance criteria

### Requirement assessment

- [ ] Buyer can create an assessment.
- [ ] Buyer can upload a text-based PDF.
- [ ] Buyer can provide requirements through chat.
- [ ] Buyer can use the guided form.
- [ ] System extracts multiple requirements.
- [ ] Buyer can edit extracted requirements.
- [ ] Assessment uses confirmed requirements.
- [ ] Every assessed requirement has one defined status.
- [ ] Supported claims show evidence references.
- [ ] Unknown claims are not fabricated.
- [ ] Buyer can change a requirement and rerun assessment.
- [ ] Previous assessment version remains accessible.
- [ ] PDF report can be downloaded.

### Seller workflow

- [ ] Seller sees only buyer-shared assessments.
- [ ] Seller can inspect requirements and evidence.
- [ ] Seller can respond to a requirement or follow-up.
- [ ] Seller cannot silently modify buyer requirements.
- [ ] Buyer can request a follow-up.

### RAG chatbot

- [ ] User can ask a natural-language product question.
- [ ] System searches official knowledge.
- [ ] System searches approved resolved-query knowledge.
- [ ] Answer includes source citations.
- [ ] Weak/no evidence does not produce a confident invented answer.
- [ ] Unanswered question can create a ticket.
- [ ] Similar approved answer can be reused.
- [ ] Similar open ticket can be detected.

### Dynamic knowledge lifecycle

- [ ] Admin can view tickets.
- [ ] Admin can submit a proposed answer.
- [ ] Answer requires approval before indexing.
- [ ] Approved answer is embedded and stored in Qdrant.
- [ ] Future query can retrieve the new answer.
- [ ] Rejected answer is not indexed.
- [ ] Updated/revoked knowledge can be excluded from retrieval.
- [ ] Official and resolved-query collections remain separate.

### Privacy

- [ ] Buyer assessment is private by default.
- [ ] Seller access requires explicit sharing.
- [ ] Private buyer data is not automatically added to global knowledge.
- [ ] API secrets are not exposed in frontend code.

---

## 12. Testing and demo scenarios

Prepare a fictional buyer named FinBank with requirements such as:
- On-premises deployment.
- Data must remain in buyer-controlled infrastructure.
- Air-gapped deployment.
- Existing ingestion pipeline compatibility.
- Granular access controls.
- A specific compliance certification.
- Migration effort estimate.

Important: verify each IOMETE capability against actual official documentation before presenting it as supported. Use unknown/needs-validation for anything not established.

Demo sequence:
1. Buyer uploads a requirement PDF.
2. System extracts structured requirements.
3. Buyer edits one requirement.
4. System assesses the requirements with evidence.
5. Buyer downloads the PDF report.
6. Buyer shares the assessment with the seller.
7. Seller sees gaps and responds to one requirement.
8. A buyer asks the product chatbot an answerable question.
9. Chatbot retrieves an official source and cites it.
10. Buyer asks a question absent from the knowledge base.
11. System creates a ticket.
12. Admin submits and approves an answer.
13. Qdrant receives the new vector.
14. A repeated question retrieves the approved answer.

The final two steps are particularly important to demonstrate the dynamic knowledge loop.

---

## 13. Implementation instructions for the coding agent

Before coding:
1. Inspect the existing repository and identify the current stack.
2. Preserve working code and avoid unnecessary rewrites.
3. Confirm the chosen OKF specification and bundle structure.
4. Create a concise implementation plan and shared data contracts.
5. Implement the smallest end-to-end vertical slice first.

Development order:
1. Project setup, database and Qdrant.
2. Official OKF ingestion.
3. RAG question-answering with citations.
4. Ticket creation and admin approval.
5. Approved answer indexing and repeat-query retrieval.
6. Buyer requirement input and extraction.
7. Requirement evidence assessment.
8. Dynamic requirement editing/reassessment.
9. PDF report.
10. Seller shared-assessment view and follow-up.
11. UI polish and demo testing.

Agent behaviour:
- Do not stop after producing scaffolding; implement working functionality.
- Do not create mock success states for features that are not implemented.
- Do not hardcode unsupported IOMETE claims.
- Do not silently substitute a different database or knowledge format.
- If a dependency is unavailable, document the blocker and implement the simplest honest fallback.
- Add tests for the critical path.
- Keep `.env.example`, setup instructions and run commands current.
- At completion, report what works, what is incomplete, how to run it and known limitations.

### Definition of done

The MVP is done when a buyer can submit requirements, receive a cited assessment, modify and reassess it, share it with a seller, and ask a product question that either receives a grounded answer or enters the human ticket-resolution process. An approved ticket must become retrievable for a future query.
