---
type: Product Documentation Summary
title: "Apache Iceberg tables"
description: "How IOMETE uses Apache Iceberg as its default table format."
resource: https://iomete.com/resources/reference/iceberg-tables/getting-started
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/reference/iceberg-tables/getting-started
    title: "Getting started with Apache Iceberg"
knowledge_id: iomete.architecture.iceberg
category: architecture
source_type: official
source_url: https://iomete.com/resources/reference/iceberg-tables/getting-started
source_document: "Getting started with Apache Iceberg"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Apache Iceberg tables

## Summary

IOMETE uses Apache Spark as its compute engine with Apache Iceberg as the table format, and Iceberg
is the default provider for new tables. The documentation lists Iceberg features including ACID
transactions, schema evolution, hidden partitioning, partition layout evolution, time travel and
version rollback.

## Details

- CREATE TABLE without USING creates an Iceberg table by default.
- Features: ACID insert/merge/delete, schema evolution, hidden partitioning, time travel, version rollback.

## Source excerpts

> IOMETE uses Apache Spark as a compute engine, with Apache Iceberg provider with additional optimization and packaging.

Source: https://iomete.com/resources/reference/iceberg-tables/getting-started

> ACID transactions and insert/merge/delete

Source: https://iomete.com/resources/reference/iceberg-tables/getting-started

> Time travel enables reproducible queries that use exactly the same table snapshot, or lets users easily examine changes

Source: https://iomete.com/resources/reference/iceberg-tables/getting-started

## Not stated in the documentation

- Nothing noted.
