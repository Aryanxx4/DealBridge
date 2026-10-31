# DealBridge

**Enterprise Product Evaluation & Intelligence Platform**

> **Build status:** this repository contains a working implementation. See [Implementation guide](#implementation-guide) for the current status, setup and run instructions, and `docs/FINAL_REPORT.md` for verified results.

DealBridge helps potential buyers evaluate whether a complex enterprise product fits their needs, while helping sellers understand buyer requirements and resolve technical questions. It combines a requirement assessment workflow with a source-grounded product knowledge assistant and a human-approved, continuously improving knowledge base.

> **One-line summary:** DealBridge turns buyer requirements and product questions into evidence-backed assessments, clear next steps and reusable verified knowledge.

---

## Table of contents

1. [The problem](#1-the-problem)
2. [The solution](#2-the-solution)
3. [Who uses DealBridge](#3-who-uses-dealbridge)
4. [The two major components](#4-the-two-major-components)
5. [Part 1: Requirement Intelligence Engine](#5-part-1-requirement-intelligence-engine)
6. [Part 2: Dynamic Product Knowledge Engine](#6-part-2-dynamic-product-knowledge-engine)
7. [How the two components work together](#7-how-the-two-components-work-together)
8. [Knowledge architecture: OKF and Qdrant](#8-knowledge-architecture-okf-and-qdrant)
9. [End-to-end example](#9-end-to-end-example)
10. [System architecture](#10-system-architecture)
11. [Technology stack](#11-technology-stack)
12. [Data and privacy principles](#12-data-and-privacy-principles)
13. [Project structure](#13-project-structure)
14. [Local setup](#14-local-setup)
15. [Environment variables](#15-environment-variables)
16. [Running the application](#16-running-the-application)
17. [Demo walkthrough](#17-demo-walkthrough)
18. [Limitations and responsible use](#18-limitations-and-responsible-use)
19. [Future roadmap](#19-future-roadmap)
20. [Project terminology](#20-project-terminology)

---

## 1. The problem

Enterprise software is difficult to evaluate and buy.

A potential customer may know the outcome they want but may not know which technical capabilities, deployment options, tools or constraints matter. Their requirements are often scattered across PDFs, spreadsheets, chat messages, forms and meetings.

A seller faces the opposite problem. They have product documentation and technical expertise, but must repeatedly interpret buyer requirements, locate relevant evidence, answer similar questions and coordinate with engineering or product teams when the answer is unclear.

Two related problems emerge.

### 1.1 Buyers struggle to express and evaluate their needs

A buyer may say:

- We need a self-hosted analytics platform.
- Our data cannot leave our infrastructure.
- We need to integrate with our existing data pipelines.
- We require granular access control.
- We have specific security and compliance requirements.

These statements are not yet a complete technical evaluation. They need to be clarified, structured and compared with actual product capabilities.

Without a structured process, buyers may:
- Miss important requirements.
- Misunderstand technical terminology.
- Receive generic sales responses.
- Struggle to distinguish documented capabilities from assumptions.
- Have difficulty presenting an evaluation to their technical or procurement teams.

### 1.2 Sellers repeatedly answer product questions

A seller may receive similar questions from multiple potential customers:

- Can the platform run on-premises?
- What deployment options are available?
- How does its architecture work?
- Which technologies does it use?
- What security capabilities are documented?
- Does it support a particular integration?

Answers may exist in documentation, but finding and explaining the correct material takes time.

Some questions may not have a clear answer in the current knowledge base. They need review by a developer, product expert or security specialist.

If those answers are resolved but never captured in reusable knowledge, the same work happens again.

### 1.3 The underlying opportunity

The problem is not simply a lack of a chatbot.

The opportunity is to connect the complete evaluation journey:

**Buyer needs → structured requirements → product evidence → fit assessment → unresolved questions → human resolution → reusable knowledge.**

---

## 2. The solution

DealBridge provides two connected capabilities.

### Part 1: Requirement Intelligence Engine

A buyer can upload a requirements PDF, describe needs in chat or fill out a guided form. DealBridge extracts and structures the requirements, checks them against product knowledge and generates an assessment.

The buyer can edit requirements and rerun the assessment. They can download a PDF report and explicitly share it with the seller.

The seller can inspect the shared requirements, understand what is supported or unresolved, provide responses and follow up with the buyer.

### Part 2: Dynamic Product Knowledge Engine

A potential buyer can ask questions in an interactive product chatbot.

DealBridge searches two knowledge sources:
1. Official product knowledge maintained in an OKF bundle.
2. Approved resolved-query knowledge stored in Qdrant.

If adequate evidence exists, DealBridge generates an answer with citations.

If the answer cannot be verified, DealBridge does not guess. It creates a ticket for an authorised developer or product expert. Once the response is reviewed and approved, it is embedded and added to the resolved-query collection. Future users can retrieve it.

### 2.1 The product promise

DealBridge does not promise that every product will fit every buyer.

It helps buyers reach a more informed decision and helps sellers identify and resolve the questions that stand between a buyer and that decision.

---

## 3. Who uses DealBridge

### 3.1 Buyer

The buyer is a prospective customer evaluating a product.

Their goals:
- Explain what they need.
- Understand the product.
- Identify matching and missing capabilities.
- Get evidence for technical claims.
- Clarify uncertain requirements.
- Share an evaluation with the seller.
- Obtain a structured report for internal analysis.

### 3.2 Seller

The seller is a vendor representative, sales engineer or solutions team member.

Their goals:
- Understand buyer requirements quickly.
- See which requirements are supported by available evidence.
- Identify questions that need technical validation.
- Provide product documentation and clarifications.
- Follow up with the buyer.
- Avoid repeatedly researching the same questions.

### 3.3 Admin / Developer / Product Expert

This role resolves unanswered questions.

Their goals:
- Review unanswered questions.
- Understand why retrieval failed.
- Provide a verified response.
- Attach supporting evidence.
- Approve and publish reusable knowledge.
- Maintain the quality of the knowledge base.

---

## 4. The two major components

```text
                         DEALBRIDGE
                              |
              +---------------+---------------+
              |                               |
              v                               v
   REQUIREMENT INTELLIGENCE         DYNAMIC PRODUCT KNOWLEDGE
          ENGINE                           ENGINE
              |                               |
       +------+-------+                 +-----+------+
       |              |                 |            |
       v              v                 v            v
     Buyer          Seller           Chatbot      Admin
       |              |                 |            |
       +-------+------+                 +-----+------+
               |                              |
               +--------------+---------------+
                              |
                    SHARED KNOWLEDGE LAYER
                              |
                  OKF + Qdrant + PostgreSQL
```

The two engines have different user experiences and responsibilities, but share the product knowledge infrastructure.

---

## 5. Part 1: Requirement Intelligence Engine

The Requirement Intelligence Engine converts a buyer's needs into a structured, evidence-backed product evaluation.

### 5.1 Buyer input methods

#### A. PDF upload

A buyer uploads a PDF containing requirements, a request for proposal, technical specifications or a list of demands.

The system:
1. Validates the file.
2. Extracts text.
3. Identifies requirement statements.
4. Categorises requirements.
5. Preserves source references where available.
6. Presents extracted requirements for review.

Scanned PDFs may require OCR. If OCR is not implemented, the interface must clearly explain that the file could not be read.

#### B. Chat-based input

The buyer can explain needs in natural language.

Example:

> We are a financial services company. We need an analytics platform that can run in our own infrastructure. We process large amounts of data and need strong access control. We also want to use our existing data pipelines.

DealBridge extracts multiple requirements from the message and may ask clarifying questions.

The system should not silently turn an assumption into a confirmed requirement.

#### C. Guided form

A structured form helps buyers provide details they might otherwise forget.

Possible fields:
- Industry and organisation context.
- Intended use case.
- Deployment preference.
- Data sovereignty requirements.
- Existing infrastructure and technologies.
- Integrations.
- Security and access-control needs.
- Compliance requirements.
- Performance and scalability needs.
- Budget and operational constraints.
- Additional free-text demands.

The form is a starting point. Buyers can add requirements that do not fit predefined categories.

### 5.2 Structured requirement extraction

Unstructured input is converted into structured records.

Example input:

> We need an analytics platform that runs on-premises, keeps all data within our infrastructure and supports our existing ingestion pipelines.

Example structured output:

| ID | Requirement | Category | Priority |
|---|---|---|---|
| REQ-001 | Platform must support on-premises deployment | Deployment | High |
| REQ-002 | Data must remain in customer-controlled infrastructure | Data sovereignty | Critical |
| REQ-003 | Existing ingestion pipelines must be compatible | Integration | High |

The buyer can edit, remove or add requirements before assessment.

### 5.3 Product suitability assessment

DealBridge compares each requirement against product knowledge.

It uses five possible outcomes:

| Status | Meaning |
|---|---|
| Supported | Reliable evidence directly supports the requirement |
| Partially supported | Only part of the requirement is established |
| Needs validation | A related capability exists, but buyer-specific confirmation is required |
| Not supported | Reliable evidence indicates that the product does not satisfy the requirement |
| Unknown | There is insufficient evidence to conclude |

The distinction between unknown and not supported is critical.

A missing document does not prove that a capability does not exist.

Each result should explain:
- What the requirement means.
- What product evidence was found.
- What the evidence actually establishes.
- What remains unverified.
- What information or test is needed next.

### 5.4 Dynamic modification

Requirements can change during evaluation.

For example:

> We no longer require air-gapped deployment, but hybrid deployment is now mandatory.

DealBridge should interpret the instruction, show the proposed changes and update the structured requirement set after confirmation when needed.

It then reruns the assessment.

Previous assessment versions should remain available. This allows the buyer to understand how a change in requirements affects product fit.

### 5.5 Downloadable assessment report

The buyer can download a PDF containing:
- Assessment overview.
- Buyer context.
- Structured requirements.
- Status of every requirement.
- Evidence and source references.
- Assumptions.
- Missing information.
- Unresolved questions.
- Recommended next steps.
- Assessment version and date.

The report is intended to support further technical and procurement analysis. It is not a contractual guarantee.

### 5.6 Seller workflow

The buyer explicitly shares an assessment with the seller.

The seller sees:
- Buyer requirements.
- Requirement priorities.
- Evidence and assessment statuses.
- Questions requiring clarification.
- Technical validation needs.
- Follow-up requests.

The seller can provide responses and supporting documents.

The buyer's original requirements remain attributable to the buyer. The seller cannot silently rewrite them.

### 5.7 Buyer-seller follow-up

The buyer can request a follow-up from the seller.

For the MVP, a simple request and response workflow is sufficient:
- Buyer creates a follow-up request.
- Seller sees it in their workspace.
- Seller responds.
- Buyer can provide additional details.
- The request can be closed.

---

## 6. Part 2: Dynamic Product Knowledge Engine

This engine is an interactive product Q&A assistant, primarily intended for new or potential buyers.

It answers questions about the product, its architecture, deployment, features, tools and relevant technical concepts.

### 6.1 Example conversation

**Buyer:** What is a lakehouse?

**DealBridge:** A lakehouse combines the flexible storage approach of a data lake with the management and analytical capabilities associated with a data warehouse. In IOMETE's context, the relevant architecture uses technologies such as Apache Spark and Apache Iceberg. [The actual answer should cite verified product documentation for product-specific statements.]

**Buyer:** Can IOMETE run in our own infrastructure?

**DealBridge:** The official deployment documentation describes customer-controlled deployment options. Here is the relevant source and excerpt.

**Buyer:** Does it support a particular internal certification?

**DealBridge:** I could not verify that from the available knowledge sources. I can raise this question for review by the product team.

This is an intentional product behaviour. An honest unknown is better than an invented answer.

### 6.2 RAG pipeline

RAG means Retrieval-Augmented Generation.

Instead of relying only on what an LLM remembers from training, the system retrieves relevant information from a maintained knowledge base and uses that information to construct its response.

The basic workflow:

```text
User question
     |
     v
Question normalisation
     |
     v
Generate query embedding
     |
     v
Semantic search in Qdrant
     |
     +--------------------------+
     |                          |
     v                          v
Official product           Resolved-query
knowledge                  knowledge
     |                          |
     +------------+-------------+
                  |
                  v
          Evidence validation
                  |
           +------+------+
           |             |
           v             v
     Adequate evidence   Insufficient evidence
           |             |
           v             v
     Grounded answer   Create ticket
     with citations        |
                           v
                    Expert resolution
                           |
                           v
                     Human approval
                           |
                           v
                     Create embedding
                           |
                           v
                  Update Qdrant collection
                           |
                           v
                 Reusable future knowledge
```

### 6.3 Why semantic search?

A user may phrase a question differently from the wording used in the documentation.

For example:

- "Can I run it without internet?"
- "Does it support air-gapped deployment?"
- "Can the platform work in an isolated environment?"

These may refer to the same underlying concept.

Semantic search compares the meaning represented by embeddings rather than relying only on exact keyword matches.

However, similarity is not proof that a source answers the question. The system must validate the retrieved evidence before generating a factual answer.

---

## 7. How the two components work together

The two components are designed to complement each other.

Consider a buyer evaluating IOMETE.

1. The buyer uploads a requirements document.
2. The Requirement Intelligence Engine extracts the requirements.
3. The engine retrieves relevant IOMETE knowledge.
4. It produces an evidence-backed assessment.
5. The buyer notices an unknown requirement.
6. The buyer opens the Product Knowledge Chatbot and asks a question.
7. If the knowledge engine cannot verify the answer, it creates a ticket.
8. An authorised expert reviews and resolves the ticket.
9. The approved answer is indexed in Qdrant.
10. The buyer can ask again and retrieve the new approved knowledge.
11. The requirement can be reassessed using the newly available evidence.
12. The buyer shares the updated assessment with the seller.

This creates a continuous relationship between requirement evaluation and product knowledge.

---

## 8. Knowledge architecture: OKF and Qdrant

A key architectural choice is to separate the human-maintained source of knowledge from the database used for semantic retrieval.

### 8.1 Official product knowledge: OKF bundle

DealBridge uses Open Knowledge Format (OKF) as the canonical, human-readable format for curated official product knowledge.

An OKF bundle organises knowledge into Markdown files with a defined structure. The exact bundle structure and metadata must follow the selected OKF specification.

Why use OKF?
- Human-readable and editable.
- Easy to review.
- Suitable for Git version control.
- Changes can be tracked.
- Individual knowledge files can be updated.
- Product knowledge remains independent of the vector database.

Example conceptual layout:

```text
knowledge/
└── official/
    └── iomete/
        ├── README.md
        ├── INDEX.md
        ├── deployment/
        │   ├── on-premises.md
        │   ├── cloud-deployment.md
        │   └── air-gapped.md
        ├── architecture/
        │   ├── lakehouse.md
        │   ├── apache-spark.md
        │   └── apache-iceberg.md
        ├── security/
        │   ├── authentication.md
        │   ├── authorization.md
        │   └── data-security.md
        └── platform/
            ├── analytics.md
            └── data-management.md
```

This is an illustrative content layout. It must be adapted to the actual OKF specification rather than treated as a formal OKF schema.

Each knowledge item should preserve:
- Title.
- Description.
- Category.
- Content.
- Source URL.
- Last verified date.
- Version.
- Approval status.

Official knowledge must be based on actual product documentation. The system must not fabricate missing information.

### 8.2 Resolved-query knowledge: Qdrant

Qdrant is the dedicated vector database used for approved resolved-query knowledge.

Why Qdrant?
- Open-source and self-hostable.
- Persistent vector storage.
- Metadata filtering.
- Dedicated retrieval API.
- Suitable for a separate semantic search service.
- Can run locally using Docker for the hackathon.

Official resources:
- [Qdrant documentation](https://qdrant.tech/documentation/)
- [Qdrant GitHub](https://github.com/qdrant/qdrant)

### 8.3 Two separate collections

DealBridge should initially maintain two Qdrant collections:

**`official_product_knowledge`**

Contains chunks ingested from the official OKF bundle.

**`resolved_query_knowledge`**

Contains approved questions and answers contributed through the ticket-resolution workflow.

The collections are separate because the source authority, update lifecycle and review process are different.

### 8.4 Ingestion of official knowledge

```text
OKF bundle
   |
   v
Bundle parser and validator
   |
   v
Markdown extraction
   |
   v
Semantic chunking
   |
   v
Embedding generation
   |
   v
Qdrant: official_product_knowledge
```

When an official knowledge file changes:
- Detect the change using a content hash.
- Reprocess only affected files/chunks.
- Update or remove stale vector records.
- Preserve source and version metadata.

### 8.5 Resolved-query knowledge lifecycle

```text
Unanswered question
       |
       v
Ticket creation
       |
       v
Expert review
       |
       v
Proposed answer
       |
       v
Human approval
       |
       v
Store approved knowledge record
       |
       v
Generate embedding
       |
       v
Qdrant: resolved_query_knowledge
       |
       v
Future semantic retrieval
```

An unanswered question must not automatically become trusted knowledge.

The developer's answer must be reviewed and approved before indexing.

This is the controlled self-updating mechanism.

### 8.6 Duplicate query detection

Different users may ask the same question using different words.

DealBridge should search existing approved answers and open tickets before creating a new ticket.

Example:

- "Can it run on our own servers?"
- "Does it support on-premises deployment?"
- "Can we host it inside our infrastructure?"

The system can identify these as potentially related questions.

However, similar wording does not always mean identical technical requirements. Product version, deployment environment and customer-specific context must be considered before reusing an answer.

---

## 9. End-to-end example

Consider a fictional organisation called FinBank evaluating IOMETE.

### Step 1: Buyer submits requirements

FinBank uploads a PDF containing:

1. On-premises deployment.
2. Data must remain in customer-controlled infrastructure.
3. Air-gapped deployment.
4. Existing data pipeline compatibility.
5. Granular access control.
6. A specific internal compliance certification.

### Step 2: Requirements are extracted

DealBridge produces structured requirement records and asks the buyer to verify them.

### Step 3: Product assessment

The system checks the requirements against the official knowledge base.

Illustrative results:

| Requirement | Example assessment |
|---|---|
| On-premises deployment | Supported, if documented |
| Customer-controlled infrastructure | Supported, if documented |
| Air-gapped deployment | Supported, if documented |
| Specific pipeline compatibility | Needs validation |
| Granular access control | Requires evidence assessment |
| Specific certification | Unknown until verified |

These are demonstration examples, not claims that any specific IOMETE capability or certification has been independently verified.

### Step 4: Buyer gets a report

FinBank downloads a PDF containing the assessment, sources, unresolved questions and next steps.

### Step 5: Buyer shares it with the seller

The seller sees the requirements and identifies which questions need engineering or security-team input.

### Step 6: Buyer asks an unanswered question

FinBank asks the Product Knowledge Chatbot about the certification.

No verified evidence is found, so a ticket is created.

### Step 7: Expert resolves the question

An authorised expert reviews the ticket, provides an answer and attaches supporting evidence.

### Step 8: Approval and knowledge update

The answer is approved, embedded and added to Qdrant's resolved-query collection.

### Step 9: Future reuse

A future buyer asks a semantically similar question. DealBridge can retrieve the approved response instead of creating duplicate work.

Private FinBank documents and requirements are not exposed to that future buyer.

---

## 10. System architecture

### 10.1 Logical architecture

```text
FRONTEND
React + TypeScript
|
+-- Buyer workspace
|   +-- PDF upload
|   +-- Chat-based requirement input
|   +-- Guided form
|   +-- Assessment results
|   +-- PDF reports
|   +-- Follow-up requests
|
+-- Product knowledge chatbot
|   +-- Conversation interface
|   +-- Suggested questions
|   +-- Source citations
|   +-- Unanswered-query ticket flow
|
+-- Seller workspace
|   +-- Shared assessments
|   +-- Requirement review
|   +-- Responses
|   +-- Follow-up queue
|
+-- Admin workspace
    +-- Ticket queue
    +-- Answer review
    +-- Approval
    +-- Knowledge status

BACKEND
FastAPI
|
+-- Assessment service
+-- Document ingestion service
+-- Requirement extraction service
+-- Evidence retrieval service
+-- RAG orchestration service
+-- Ticket service
+-- Knowledge publication service
+-- Seller collaboration service
+-- PDF report service

DATA
|
+-- PostgreSQL
|   +-- Deals and assessments
|   +-- Requirements
|   +-- Results and evidence references
|   +-- Tickets
|   +-- Conversations
|   +-- Follow-ups
|
+-- Qdrant
|   +-- official_product_knowledge
|   +-- resolved_query_knowledge
|
+-- OKF bundle
    +-- Official product knowledge source
```

### 10.2 Why a modular monolith?

For the hackathon, a modular monolith is preferable to microservices.

It gives the project:
- One backend to run.
- Clear module boundaries.
- Easier integration.
- Fewer deployment dependencies.
- A simpler debugging process.

The modules can be separated into services later if the product grows.

---

## 11. Technology stack

Recommended stack:

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | Web interface |
| UI | Tailwind CSS + shadcn/ui | Styling and components |
| Backend | Python FastAPI | API and orchestration |
| Relational database | PostgreSQL | Application and workflow data |
| Vector database | Qdrant | Semantic retrieval |
| Official knowledge format | OKF | Curated product knowledge |
| LLM | Configurable LLM API | Extraction, assessment and answer generation |
| Embeddings | Consistent embedding model | Document and query vectors |
| PDF parsing | PyMuPDF or equivalent | PDF text extraction |
| Excel parsing | pandas / openpyxl | Optional questionnaire support |
| PDF export | ReportLab or equivalent | Assessment reports |
| Containerisation | Docker | Local service setup |

### Why PostgreSQL and Qdrant both?

They have different jobs.

PostgreSQL stores structured application data:
- Users.
- Assessments.
- Requirements.
- Tasks.
- Tickets.
- Messages.
- Approval history.

Qdrant stores embeddings and searchable knowledge chunks.

Do not use a vector database as a replacement for the transactional database.

### Embedding consistency

Use the same embedding model and dimensions for indexing and query generation within a collection.

If the model changes, plan a re-embedding and reindexing process.

A free/local embedding model can reduce API costs, subject to available hardware. A hosted model can be used through a configured API.

---

## 12. Data and privacy principles

DealBridge deals with potentially sensitive enterprise requirements.

Important rules:

1. Buyer assessments are private by default.
2. Sharing with a seller requires explicit buyer action.
3. Seller must not silently edit buyer requirements.
4. Private buyer documents must not be added to global knowledge.
5. Only approved resolved answers enter the reusable knowledge base.
6. Official and resolved-query sources remain distinguishable.
7. Source references must be preserved.
8. API keys must remain on the server.
9. Uploaded documents must be treated as untrusted input.
10. Production deployment requires proper authentication, access control, tenant isolation and secure storage.

The hackathon prototype may use demo identities and a simplified role switcher, but it must not present that as production-grade access control.

---

## 13. Project structure

An illustrative repository structure:

```text
dealbridge/
|
+-- frontend/
|   +-- src/
|       +-- components/
|       +-- pages/
|       |   +-- buyer/
|       |   +-- seller/
|       |   +-- admin/
|       |   +-- chatbot/
|       +-- services/
|       +-- hooks/
|       +-- types/
|
+-- backend/
|   +-- app/
|       +-- api/
|       +-- models/
|       +-- schemas/
|       +-- services/
|       |   +-- assessment/
|       |   +-- ingestion/
|       |   +-- retrieval/
|       |   +-- rag/
|       |   +-- tickets/
|       |   +-- knowledge/
|       |   +-- reports/
|       +-- repositories/
|       +-- prompts/
|       +-- core/
|       +-- main.py
|
+-- knowledge/
|   +-- official/
|       +-- iomete/
|           +-- [OKF bundle files]
|
+-- scripts/
|   +-- ingest_okf.py
|   +-- reindex_knowledge.py
|
+-- tests/
|
+-- docker-compose.yml
+-- .env.example
+-- README.md
+-- REQUIREMENTS.md
```

The coding agent should adapt this structure to the actual repository rather than blindly replacing an existing working structure.

---

## 14. Local setup

The exact commands depend on the final repository and dependency files. The following describes the intended setup.

### Prerequisites

- Python 3.11+ (or the version selected by the project).
- Node.js LTS.
- npm.
- Docker and Docker Compose.
- PostgreSQL.
- Qdrant.
- An LLM API key if using a hosted model.

### Start infrastructure

A local Docker Compose setup should start:
- PostgreSQL.
- Qdrant.

Persist data using Docker volumes so that approved knowledge and application records survive restarts.

### Install backend dependencies

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Install frontend dependencies

```bash
cd frontend
npm install
```

### Configure environment

Copy `.env.example` to `.env` and populate required values.

Never commit the real `.env` file.

---

## 15. Environment variables

The implementation should document variables similar to:

```env
# Application
APP_ENV=development
APP_SECRET_KEY=change-me
BACKEND_PORT=8000

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/dealbridge

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_OFFICIAL_COLLECTION=official_product_knowledge
QDRANT_RESOLVED_COLLECTION=resolved_query_knowledge

# LLM
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

# Embeddings
EMBEDDING_PROVIDER=
EMBEDDING_API_KEY=
EMBEDDING_MODEL=
EMBEDDING_DIMENSION=

# File storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=20
```

These are suggested variable names. The final implementation should use a consistent configuration system and document which values are required.

---

## 16. Running the application

The final repository should provide simple commands, ideally:

```bash
# Start infrastructure
docker compose up -d

# Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Start frontend in another terminal
cd frontend
npm run dev
```

The repository should also provide:
- Database migration/setup instructions.
- Qdrant collection initialisation.
- OKF ingestion command.
- Demo seed-data command if applicable.
- Test command.

Do not claim that a command works until it has been tested in the repository.

---

## 17. Demo walkthrough

The strongest demonstration should show the two components working together.

### Scene 1: Buyer starts an evaluation

A fictional buyer, FinBank, opens DealBridge and uploads a requirements PDF.

### Scene 2: Requirements are structured

DealBridge extracts the requirements and displays them in an editable table.

### Scene 3: Buyer modifies a requirement

The buyer changes a deployment requirement through chat or the form. DealBridge updates the assessment.

### Scene 4: Evidence-backed assessment

DealBridge retrieves official product evidence and classifies each requirement.

### Scene 5: Report generation

The buyer downloads the PDF assessment report.

### Scene 6: Seller collaboration

The buyer shares the assessment. The seller sees requirements and unresolved gaps.

### Scene 7: Product chatbot

The buyer asks a product question. DealBridge retrieves official documentation and cites it.

### Scene 8: Unanswered question

The buyer asks a question for which the system has no adequate evidence. A ticket is created instead of an invented answer.

### Scene 9: Expert resolution

The admin submits and approves a response with supporting evidence.

### Scene 10: Dynamic knowledge update

The approved response is embedded and published to Qdrant.

### Scene 11: Repeated question

A similar question is asked again. DealBridge retrieves the approved resolution.

This demonstrates the complete knowledge lifecycle, not just a chatbot response.

---

## 18. Limitations and responsible use

DealBridge is an evaluation assistant, not an autonomous procurement authority.

Its assessment depends on:
- Completeness of the buyer's requirements.
- Quality and currency of product documentation.
- Retrieval quality.
- Human validation of uncertain requirements.
- Accuracy of expert-provided answers.

A retrieved passage may be relevant without fully satisfying a requirement.

Therefore:
- A similarity score must never be presented as proof.
- Unknown must remain unknown.
- Unsupported must be used only when reliable evidence establishes non-support.
- Certification claims require explicit evidence.
- Buyer-specific compatibility requires buyer-specific validation.
- Reports must explain assumptions and limitations.

For a production enterprise deployment, additional security, privacy, access-control and audit work is required.

---

## 19. Future roadmap

Potential future improvements:

### Knowledge management
- Automatic documentation change detection.
- Git-based OKF publishing pipeline.
- Knowledge expiry and review reminders.
- Conflicting-source detection.
- Knowledge quality dashboards.

### Buyer experience
- More sophisticated requirement discovery.
- Requirement templates by industry.
- Assessment comparison across products.
- More detailed architecture recommendations.
- Stakeholder-specific reports.

### Seller experience
- CRM integration.
- Automated call preparation.
- Technical validation task management.
- Sales engineering workflow integration.
- Email and calendar integrations.

### RAG improvements
- Hybrid keyword and semantic search.
- Reranking.
- Query clustering.
- Advanced duplicate detection.
- Retrieval evaluation datasets.
- Model and prompt evaluation.

### Enterprise readiness
- Multi-tenant architecture.
- Role-based access control.
- Audit logs.
- Secure document storage.
- Configurable retention.
- Deployment in customer-controlled infrastructure.

---

## 20. Project terminology

| Term | Meaning |
|---|---|
| Requirement | A buyer's stated need or constraint |
| Assessment | Evaluation of requirements against available product evidence |
| Evidence | A source excerpt supporting or limiting a product claim |
| RAG | Retrieval-Augmented Generation |
| Embedding | Numerical representation of text used for semantic retrieval |
| Vector database | Database that stores and searches embeddings |
| Qdrant | The vector database used by DealBridge |
| OKF bundle | Human-readable, structured knowledge source used for official product knowledge |
| Official knowledge | Curated product information based on authoritative documentation |
| Resolved-query knowledge | Human-reviewed answers to previously unanswered questions |
| Ticket | A query requiring human investigation or clarification |
| Semantic search | Retrieval based on meaning rather than exact wording |
| Reindexing | Updating vector records after source content changes |
| Grounded answer | An answer supported by retrieved evidence |
| Unknown | Insufficient evidence to conclude |
| Needs validation | More technical or buyer-specific verification is required |

---

## Final summary

DealBridge brings together two parts of the enterprise buying journey.

The Requirement Intelligence Engine helps a buyer explain what they need, understand how a product maps to those needs and collaborate with the seller.

The Dynamic Product Knowledge Engine helps potential buyers understand the product through evidence-backed answers. When it cannot answer reliably, it creates a human-resolution workflow and makes approved answers reusable.

The knowledge architecture intentionally separates:
- Official product knowledge, maintained as an OKF bundle.
- Approved resolved-query knowledge, stored in Qdrant.
- Transactional application data, stored in PostgreSQL.

Together, these components turn DealBridge into a platform for structured product evaluation, buyer-seller collaboration and continuously improving product knowledge.

---

# Implementation guide

The sections below describe the implementation in this repository (hackCbs9). They were written after running every listed command in this repository.

## Current status

**Works, verified by automated tests against real PostgreSQL, Qdrant and the local embedding model, with a scripted LLM:**
- Official knowledge: an OKF v0.2 bundle of 44 curated IOMETE concepts, every excerpt verified verbatim against the live documentation page, and idempotent ingestion (89 chunks).
- Grounded product chat: classification, retrieval over both collections with the mandatory approved and ACTIVE filter, verbatim quote verification, a faithfulness check, labelled citations, tickets with dedupe, and My questions.
- Dynamic knowledge loop: the admin ticket workflow, approval-gated publishing into `resolved_query_knowledge`, supersede and revoke, and a differently worded repeat question answered as "Expert-verified answer".
- Requirement intake by PDF (scanned detection), intake chat with apply-only-on-click proposals, and the guided form. RequirementService with revisions, STALE handling and confirmation rules.
- The assessment engine with judge, guardrails G1–G8 and immutable versions, plus comparison, the PDF report, explicit version-bound sharing, the seller workspace, seller responses and follow-ups.
- P1 extras: Excel export, seller document uploads (labelled seller-provided, never indexed), internal follow-up owners, a changed-only version comparison and dashboard filters.
- `make test`: 118 backend tests pass, plus frontend typecheck, lint and build. `make check-secrets` passes. A clean clone was verified: `git clone`, then the setup commands below, then `make test` and `make check-secrets` all succeeded.

**Not yet verified with the real language model.** The Qwen API key has not been provided yet. Without it every LLM endpoint returns 503 `LLM_NOT_CONFIGURED` and the UI says so. The real-LLM demo run (`demo/DEMO_SCRIPT.md`) and `make test-llm` are pending. See `docs/FINAL_REPORT.md`, "Needs the user".

## Architecture

```text
 Browser (React 18 + Vite, demo identity header)            knowledge/official/iomete  (OKF v0.2 bundle, Git)
        │  /api (Vite proxy)                                          │ scripts/ingest_okf.py (hash-based, idempotent)
        ▼                                                             ▼
 FastAPI (sync) ── RequirementService · RAG pipeline · judge + guardrails · publish ──► Qdrant
    │      │        jobs (BackgroundTasks + jobs table)                                 ├─ official_product_knowledge
    │      └──► Qwen (DashScope OpenAI-compatible API, forced tool calls)              └─ resolved_query_knowledge
    │      └──► fastembed BAAI/bge-small-en-v1.5 (local, 384 d)      (filter: approval_status=approved AND validity_status=ACTIVE)
    ▼
 PostgreSQL 16: users, assessments, requirements, revisions, versions, evidence, tickets, knowledge_records,
                shares, follow-ups, jobs, audit_events, knowledge_state (epoch), okf_files, ingestion_runs
```

## Prerequisites
- Python 3.12 (`python3.12` on PATH; tested with Homebrew Python 3.12.15)
- Node.js 20+ and npm (tested with Node 22.16, npm 10.9)
- Docker with Compose v2 (tested with Docker 29 on Colima, Compose 5.6)
- About 200 MB for the embedding model, downloaded on first use into `.cache/fastembed`

## Setup
```bash
cp .env.example .env          # then set LLM_API_KEY to your Qwen (DashScope) key; never commit .env
make up                       # postgres (host port 5433) + qdrant (6333/6334), waits until healthy
make backend-install          # creates backend/.venv and installs pinned requirements
make frontend-install         # npm ci
make migrate                  # alembic upgrade head
make init-vector              # creates both Qdrant collections and payload indexes (idempotent)
make ingest                   # ingests the OKF bundle (second run upserts 0 points)
make seed                     # demo identities (idempotent)
```

## Run
```bash
make dev-backend              # http://localhost:8000  (OpenAPI docs: /docs, health: /api/health)
make dev-frontend             # http://localhost:5173
```
Pick an identity with the dropdown in the top bar (Priya, buyer · Daniel, buyer · Meera and Arjun, seller · Sam, admin).

## Environment variables
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql+psycopg://dealbridge:dealbridge@localhost:5433/dealbridge` | PostgreSQL (psycopg 3) |
| `QDRANT_URL` | yes | `http://localhost:6333` | Qdrant REST |
| `APP_SECRET_KEY` | yes | `change-me` | Required setting; never logged |
| `LLM_API_KEY` | for LLM features | empty | Qwen / DashScope key. Empty means LLM endpoints return 503 `LLM_NOT_CONFIGURED` |
| `LLM_PROVIDER` | no | `qwen` | Only `qwen` is accepted |
| `LLM_BASE_URL` | no | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible endpoint |
| `LLM_MODEL` / `LLM_FAST_MODEL` | no | `qwen3.8-max` / `qwen3.8-flash` | Main and fast models |
| `LLM_TIMEOUT_SECONDS`, `LLM_FAST_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | no | 60 / 20 / 2 | Timeouts and retries |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `FASTEMBED_CACHE_DIR` | no | `fastembed`, `BAAI/bge-small-en-v1.5`, 384, `./.cache/fastembed` | Local embeddings (changing them requires a reindex) |
| `RETRIEVAL_MIN_SCORE`, `RESOLVED_REUSE_MIN_SCORE` | no | 0.60 / 0.70 | Calibrated thresholds (see below) |
| `TOP_K_OFFICIAL`, `TOP_K_RESOLVED`, `TICKET_DUP_MIN_SCORE` | no | 6 / 4 / 0.85 | Retrieval and dedupe |
| `ENABLE_FAITHFULNESS_CHECK`, `ALLOW_SELF_APPROVAL` | no | true / true | Second-stage check; one admin may propose and approve (both recorded) |
| `UPLOAD_DIR`, `MAX_UPLOAD_MB`, `MAX_PDF_PAGES` | no | `./uploads`, 20, 200 | Upload storage and limits |
| `OKF_BUNDLE_DIR` | no | `./knowledge/official/iomete` | OKF bundle root |
| `APP_ENV`, `BACKEND_PORT`, `FRONTEND_ORIGIN`, `LOG_LEVEL` | no | development, 8000, `http://localhost:5173`, INFO | App settings (CORS allows only `FRONTEND_ORIGIN`) |
| `QDRANT_API_KEY`, `QDRANT_OFFICIAL_COLLECTION`, `QDRANT_RESOLVED_COLLECTION` | no | empty, defaults | Qdrant options |

The frontend has one variable, `VITE_API_BASE_URL` (default `/api`). No secret is ever placed in `frontend/`.

## Knowledge: OKF status and how to add or update knowledge
The official knowledge is an **Open Knowledge Format v0.2** bundle (spec: GoogleCloudPlatform/open-knowledge-format, `SPEC.md` at commit `ad30107`). See `knowledge/official/OKF_CONFORMANCE.md` for the field mapping and `knowledge/official/README.md` for the update workflow:
1. Edit or add a concept in `knowledge/official/iomete/<category>/`, from a fetched official page only, and bump `version`.
2. Run `backend/.venv/bin/python scripts/verify_knowledge_excerpts.py`. It fetches each source page and checks every excerpt verbatim. Add `--approve` to approve the files that pass.
3. Run `make ingest`. Only changed files are re-embedded. `python scripts/ingest_okf.py --validate-only | --dry-run | --force | --recreate | --rebuild-index`.
4. After changing the embedding model: `python scripts/reindex_knowledge.py` (official is rebuilt from the bundle, resolved from PostgreSQL).

Known documentation gaps (air-gapped installs, compliance certifications and others) are listed in `docs/KNOWLEDGE_GAPS.md`.

## Retrieval thresholds and how they were calibrated
`scripts/calibrate_threshold.py` runs 37 answerable and 17 unanswerable questions (`backend/tests/fixtures/retrieval_eval.yaml`) against the indexed bundle. No threshold reaches 90% recall at a 10% or lower false-accept rate. Off-topic questions score at most 0.47, but on-topic yet undocumented questions (MFA, HSM keys, SOC 2) score 0.66–0.71, the same as answerable ones. `RETRIEVAL_MIN_SCORE=0.60` (recall 97%, false-accept 47%) therefore only removes noise. Grounding is enforced by verbatim quote verification, the explicit-certification rule, the faithfulness check and the guardrails. The full table is in `docs/DECISIONS.md`.

## Demo walkthrough
See [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md). Run `make reset-demo` before a demo. The demo PDFs are regenerated with `backend/.venv/bin/python scripts/make_demo_pdfs.py`.

## Tests
```bash
make test            # backend pytest (unit + integration on dealbridge_test DB and test_ Qdrant collections, scripted LLM)
                     # then frontend typecheck, lint and build
make check-secrets   # builds the frontend and scans dist/ and tracked files for secrets
make test-llm        # real-LLM prompt-injection evaluation (skipped when LLM_API_KEY is empty)
```

## Troubleshooting
- **Docker not running / `make up` hangs:** start the runtime (`colima start`), then `docker compose ps`. If `docker compose` is unknown, add `"cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]` to `~/.docker/config.json`.
- **Port 5432 already in use:** the container is published on **5433** by default (`POSTGRES_HOST_PORT`) because a local PostgreSQL often owns 5432.
- **Backend exits with "Run make migrate":** the database revision is behind the code. Run `make migrate`.
- **`reindex_required` in `/api/health` or on Admin, Knowledge:** the collections were built with a different embedding model or dimension. Run `python scripts/reindex_knowledge.py`.
- **"Language model not configured" alert or 503 `LLM_NOT_CONFIGURED`:** set `LLM_API_KEY` in `.env` and restart `make dev-backend`.
- **Embedding model download is slow or fails:** the first start downloads about 130 MB from Hugging Face into `.cache/fastembed`, and `/api/health` shows `embedding_loading: true` until it finishes. Retry when the network is available; the cache is reused.

## Limitations and responsible use
DealBridge is an evaluation assistant, not an autonomous procurement authority. Its results depend on the completeness of the buyer's requirements, the quality and currency of the documentation, retrieval quality, human validation of uncertain requirements, and the accuracy of expert answers. A retrieved passage may be relevant without satisfying a requirement. Therefore similarity scores are never shown as proof, Unknown stays Unknown, Not supported is used only on explicit evidence, certification claims require explicit evidence, buyer-specific compatibility requires buyer-specific validation, and reports state their assumptions and limitations.

**Not implemented (by design for this MVP):** real authentication (demo identities only), tenant isolation beyond ownership checks, encryption at rest, data retention policies, malware scanning of uploads, and OCR for scanned PDFs. Rate limiting is in-process and not production-grade. Production use requires all of these.
