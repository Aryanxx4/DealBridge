---
type: Product Documentation Summary
title: "Lakehouse platform overview"
description: "What IOMETE is and how its decoupled compute and storage architecture works."
resource: https://iomete.com/resources/getting-started/what-is-iomete
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/getting-started/what-is-iomete
    title: "What Is IOMETE? Self-Hosted Spark + Iceberg Lakehouse"
knowledge_id: iomete.architecture.lakehouse
category: architecture
source_type: official
source_url: https://iomete.com/resources/getting-started/what-is-iomete
source_document: "What Is IOMETE? Self-Hosted Spark + Iceberg Lakehouse"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Lakehouse platform overview

## Summary

IOMETE describes itself as a data lakehouse platform for AI and analytics built on Apache Spark. It
uses a decoupled compute and storage architecture, acting as the computation, management and
governance layer over a storage layer, so compute and storage scale independently. Data formats
handled include Parquet, Avro, ORC, JSON, XML and CSV, and Apache Iceberg is the lakehouse table
format.

## Details

- Decoupled compute and storage; independent scaling.
- Lakehouse storage format: Apache Iceberg.
- Structured and semi-structured formats: Parquet, Avro, ORC, JSON, XML, CSV.
- Compute runs on Kubernetes and exposes SQL endpoints.

## Source excerpts

> IOMETE utilizes a decoupled compute and storage architecture, which allows for the independent scaling of compute and storage.

Source: https://iomete.com/resources/getting-started/what-is-iomete

> IOMETE acts as the computation, management, and governance layer that connects to the storage layer.

Source: https://iomete.com/resources/getting-started/what-is-iomete

> IOMETE runs on Kubernetes, providing Compute Clusters that expose SQL endpoints for querying large-scale data.

Source: https://iomete.com/resources/getting-started/what-is-iomete

## Not stated in the documentation

- Nothing noted.
