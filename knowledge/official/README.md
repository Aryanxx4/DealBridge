# Official product knowledge

`iomete/` is an **Open Knowledge Format (OKF) v0.2** bundle of curated IOMETE product knowledge. See `OKF_CONFORMANCE.md` for the spec version, the field mapping and the validator. This README sits outside the bundle root on purpose: OKF treats every non-reserved `.md` file inside the bundle as a concept.

## Rules
- Content comes only from pages actually fetched from the official documentation at https://iomete.com/resources/. Nothing is written from memory.
- Summaries and details are paraphrased. Only `## Source excerpts` quotes the documentation verbatim (at most 40 words each, each followed by its URL).
- `## Not stated in the documentation` is for reviewers and is never indexed.
- Only files with `approval_status: approved` (OKF `status: stable`) are indexed. Drafts are skipped, and their points are deleted if they were previously indexed.

## Adding or updating knowledge
1. Fetch the official page and write or edit the concept file. Bump `version` when the body changes. Leave `approval_status: draft` and `status: draft` until checked.
2. Run `backend/.venv/bin/python scripts/verify_knowledge_excerpts.py`. It fetches each source page and checks every excerpt verbatim.
3. Re-read the summary and details against the page. Then approve by running `scripts/verify_knowledge_excerpts.py --approve`, which marks the file machine-verified, or by editing the frontmatter after a human review. Add a `human:<id>` entry to `verified` for human sign-off.
4. Run `make ingest`. Only changed files are re-embedded. Unchanged files produce zero upserts.
5. Use `python scripts/ingest_okf.py --rebuild-index` to regenerate the `index.md` files.
