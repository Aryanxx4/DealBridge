---
type: Product Documentation Summary
title: "Spark catalogs"
description: "Managed Iceberg REST catalogs and external catalogs in IOMETE."
resource: https://iomete.com/resources/user-guide/spark-catalogs/overview
tags: [iomete, platform]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/spark-catalogs/overview
    title: "Spark Catalogs Overview"
knowledge_id: iomete.platform.spark-catalogs
category: platform
source_type: official
source_url: https://iomete.com/resources/user-guide/spark-catalogs/overview
source_document: "Spark Catalogs Overview"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Spark catalogs

## Summary

IOMETE lets users configure multiple Spark catalogs to access data from IOMETE and external sources.
Managed catalogs operate as Iceberg REST catalogs, are reachable by external tools at
/catalogs/<catalog name>, and integrate with existing data security rules for role-based access
control. External catalog types are also supported.

## Details

- Default catalog: spark_catalog.
- Authentication to managed catalogs uses a session or a personal access token.

## Source excerpts

> IOMETE allows users to configure multiple Spark Catalogs to access data from both IOMETE systems and external sources.

Source: https://iomete.com/resources/user-guide/spark-catalogs/overview

> They seamlessly integrate with existing data security rules to enforce role-based access control (RBAC).

Source: https://iomete.com/resources/user-guide/spark-catalogs/overview

## Not stated in the documentation

- Nothing noted.
