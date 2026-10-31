---
type: Product Documentation Summary
title: "Storage backends"
description: "Object storage systems IOMETE supports as its data layer."
resource: https://iomete.com/resources/getting-started/architecture
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/getting-started/architecture
    title: "IOMETE Architecture: Control Plane, Data Planes, Kubernetes"
knowledge_id: iomete.architecture.storage
category: architecture
source_type: official
source_url: https://iomete.com/resources/getting-started/architecture
source_document: "IOMETE Architecture: Control Plane, Data Planes, Kubernetes"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Storage backends

## Summary

Everything IOMETE stores, including table data, Spark event logs, SQL results and worksheets, goes
into object storage, and compute and storage are fully decoupled. Supported providers include Apache
Ozone, Dell ECS, MinIO, AWS S3, Google Cloud Storage and Azure Blob and Data Lake Storage.

## Details

- s3a:// for Apache Ozone, Dell ECS, MinIO, AWS S3; gs:// for Google Cloud Storage; wasbs:// and abfs:// for Azure.
- All platform services share a single PostgreSQL server for metadata, with separate databases created automatically.

## Source excerpts

> Everything IOMETE stores (table data, Spark event logs, SQL results, worksheets) goes into object storage. Compute and storage are fully decoupled.

Source: https://iomete.com/resources/getting-started/architecture

> All services share a single PostgreSQL server.

Source: https://iomete.com/resources/getting-started/architecture

## Not stated in the documentation

- Nothing noted.
