---
type: Product Documentation Summary
title: "Job Orchestrator"
description: "Priority-based, resource-aware scheduling of Spark jobs."
resource: https://iomete.com/resources/user-guide/spark-jobs/job-orchestrator
tags: [iomete, platform]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/spark-jobs/job-orchestrator
    title: "Job Orchestrator"
knowledge_id: iomete.platform.job-orchestrator
category: platform
source_type: official
source_url: https://iomete.com/resources/user-guide/spark-jobs/job-orchestrator
source_document: "Job Orchestrator"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Job Orchestrator

## Summary

The Job Orchestrator adds priority-based scheduling (High and Normal queues) and resource-aware
execution, submitting jobs only when cluster capacity is available. Within each priority, jobs run
in FIFO order. Each job can opt in or out individually.

## Details

- High-priority queue is processed before normal priority.
- Monitors CPU and memory availability before scheduling.

## Source excerpts

> Jobs are submitted only when cluster capacity is available, reducing the chances of failure due to insufficient compute resources.

Source: https://iomete.com/resources/user-guide/spark-jobs/job-orchestrator

> Within each priority level, jobs are processed in First-In-First-Out (FIFO) order.

Source: https://iomete.com/resources/user-guide/spark-jobs/job-orchestrator

## Not stated in the documentation

- Nothing noted.
