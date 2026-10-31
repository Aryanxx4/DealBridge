---
type: Product Documentation Summary
title: "Automated table maintenance"
description: "Background maintenance of Iceberg tables (compaction, snapshots, orphan files)."
resource: https://iomete.com/resources/user-guide/table-maintenance/overview
tags: [iomete, platform]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/table-maintenance/overview
    title: "Table Maintenance Overview"
knowledge_id: iomete.platform.table-maintenance
category: platform
source_type: official
source_url: https://iomete.com/resources/user-guide/table-maintenance/overview
source_document: "Table Maintenance Overview"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Automated table maintenance

## Summary

Table Maintenance is an automated background service that keeps Iceberg tables healthy by detecting
changed tables, evaluating configurable thresholds and executing Iceberg maintenance procedures.
Defaults are set per catalog and can be overridden per table, and each run records before-and-after
metrics.

## Details

- Pipeline: detect, evaluate, execute.
- Metrics considered include file sizes, snapshot age, delete-file ratios and manifest counts.

## Source excerpts

> Table Maintenance is an automated background service that keeps tables healthy.

Source: https://iomete.com/resources/user-guide/table-maintenance/overview

> Default rules are defined at the catalog level and can be overridden for individual tables.

Source: https://iomete.com/resources/user-guide/table-maintenance/overview

## Not stated in the documentation

- Nothing noted.
