# OKF conformance

- **Specification:** Open Knowledge Format (OKF) **v0.2**
- **Source:** https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
- **Commit read:** `ad30107c31c06aec8a7d5636e0d1058118604e6f` (fetched 2026-10-31)
- **Bundle root:** `knowledge/official/iomete/` (declares `okf_version: "0.2"` in its root `index.md`)

## How this bundle conforms (spec §11)
1. Every non-reserved `.md` file in the bundle has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type` (here `Product Documentation Summary`).
3. Reserved files: `index.md` files contain no frontmatter except the bundle-root `okf_version` key (§8, §12). `log.md` uses ISO `YYYY-MM-DD` date headings, newest first (§9).

This file and `knowledge/official/README.md` sit outside the bundle root, because OKF treats every other `.md` in the bundle as a concept document.

## Validator
The spec repository ships no standalone validator. `python scripts/ingest_okf.py --validate-only` implements the §11 rules above, plus DealBridge project rules:
- required extension keys are present
- `knowledge_id` is unique
- `category` is valid
- `source_url` is http(s)
- dates are valid
- `approval_status` is consistent with `status`
- the body sections DealBridge needs for chunking are present

## Field mapping (build prompt §8.1 to OKF)
| DealBridge field | OKF representation |
|---|---|
| knowledge_id | extension key `knowledge_id` (the OKF concept ID is the file path without `.md`; both are recorded) |
| title | `title` (OKF recommended) |
| description | `description` (OKF recommended) |
| category | extension key `category`, also in `tags` |
| source_type | extension key `source_type: official` |
| source_url | `resource` (OKF), `sources[0].resource` (OKF provenance), and extension key `source_url` |
| source_document | `sources[0].title` and extension key `source_document` |
| last_verified_at | `verified.at` (OKF trust) and extension key `last_verified_at` (date) |
| version | extension key `version` (integer) |
| approval_status | extension key `approval_status`, kept consistent with OKF `status` (approved = stable, draft = draft) |
| content_hash | not stored in files; computed at ingestion |

## Trust tier
`verified.by` is `process:dealbridge-excerpt-check`. Per spec §5.3, that tier is **machine-confirmed**, not human-reviewed. Where a human reviewer signs off, they add a `{ by: human:<id>, at: ... }` entry.
