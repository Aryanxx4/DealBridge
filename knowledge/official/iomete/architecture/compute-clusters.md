---
type: Product Documentation Summary
title: "Compute clusters"
description: "Spark-based compute clusters that serve SQL queries over shared object storage."
resource: https://iomete.com/resources/user-guide/compute-clusters/overview
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/compute-clusters/overview
    title: "Compute Clusters"
knowledge_id: iomete.architecture.compute-clusters
category: architecture
source_type: official
source_url: https://iomete.com/resources/user-guide/compute-clusters/overview
source_document: "Compute Clusters"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Compute clusters

## Summary

A compute cluster provides dedicated CPU and memory, powered by Apache Spark, for running queries.
Table data lives in S3-compatible object storage separate from compute, so several clusters can
share the same data. Clusters can be sized per workload and shut down when idle to stop accruing
costs.

## Details

- Clusters can be sized for batch ETL, interactive analytics or a dedicated BI connection.
- Auto-suspend idle timeout is shown in the cluster list.

## Source excerpts

> A compute cluster gives you dedicated CPU and memory, powered by Apache Spark, for running queries.

Source: https://iomete.com/resources/user-guide/compute-clusters/overview

> Table data lives in S3-compatible object storage, separate from compute, so multiple clusters can share the same data without interfering with each other.

Source: https://iomete.com/resources/user-guide/compute-clusters/overview

## Not stated in the documentation

- Nothing noted.
