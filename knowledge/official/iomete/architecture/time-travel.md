---
type: Product Documentation Summary
title: "Time travel on Iceberg tables"
description: "Querying historical table snapshots in IOMETE."
resource: https://iomete.com/resources/reference/iceberg-tables/time-travel
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/reference/iceberg-tables/time-travel
    title: "Time travel with SQL examples"
knowledge_id: iomete.architecture.time-travel
category: architecture
source_type: official
source_url: https://iomete.com/resources/reference/iceberg-tables/time-travel
source_document: "Time travel with SQL examples"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Time travel on Iceberg tables

## Summary

Apache Iceberg in IOMETE keeps snapshots whenever a table changes, and users can query data as it
existed at a specific point in time. The documentation describes this as useful for debugging,
auditing and historical analysis.

## Details

- Each modification creates a snapshot with a unique identifier.
- Snapshots are consistent, complete views of a table at a point in time.

## Source excerpts

> Apache Iceberg provides versioning and time travel capabilities, allowing users to query data as it existed at a specific point in time.

Source: https://iomete.com/resources/reference/iceberg-tables/time-travel

> This feature can be extremely useful for debugging, auditing, and historical analysis.

Source: https://iomete.com/resources/reference/iceberg-tables/time-travel

## Not stated in the documentation

- Nothing noted.
