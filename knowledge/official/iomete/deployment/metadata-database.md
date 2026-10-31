---
type: Product Documentation Summary
title: "Metadata database"
description: "The relational database IOMETE uses for platform and data lake metadata."
resource: https://iomete.com/resources/deployment/backend-databases
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/backend-databases
    title: "IOMETE Backend Databases"
knowledge_id: iomete.deployment.metadata-database
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/backend-databases
source_document: "IOMETE Backend Databases"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Metadata database

## Summary

IOMETE requires a backend database for two kinds of metadata: IOMETE's own internal metadata and
data lake metadata for the Hive Metastore and Iceberg Metastore. The backend databases page states
that either MySQL or PostgreSQL can be used.

## Details

- Internal metadata: clusters, Spark jobs, users and similar resources.
- Data lake metadata: databases, tables, partitions, columns.
- Load on the data lake metadata database depends on the number of users and tables.

## Source excerpts

> IOMETE requires a backend database to efficiently store and manage metadata.

Source: https://iomete.com/resources/deployment/backend-databases

> For optimal functionality, IOMETE supports the use of either MySQL or PostgreSQL databases.

Source: https://iomete.com/resources/deployment/backend-databases

## Not stated in the documentation

- The on-premises installation guide lists PostgreSQL specifically; MySQL support for current releases is not restated there.
