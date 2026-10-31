---
type: Product Documentation Summary
title: "Spark jobs and scheduling"
description: "Running batch Spark jobs in IOMETE with schedules and resource bundles."
resource: https://iomete.com/resources/user-guide/spark-jobs/creating-spark-job
tags: [iomete, platform]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/spark-jobs/creating-spark-job
    title: "Creating Spark Job"
knowledge_id: iomete.platform.spark-jobs
category: platform
source_type: official
source_url: https://iomete.com/resources/user-guide/spark-jobs/creating-spark-job
source_document: "Creating Spark Job"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Spark jobs and scheduling

## Summary

Each Spark job runs as an isolated Spark application with its own driver and optional executors.
Jobs are created from Job Templates, reference a resource bundle that defines quotas, run in a
Kubernetes namespace under a chosen user identity, and can be triggered manually, at an interval or
by a cron expression. Applications can be Python or JVM (Java, Scala).

## Details

- Trigger types: Manual, Interval, Cron.
- Concurrency for scheduled jobs: Allow, Replace or Forbid.
- An equivalent cURL command is available for API-based creation.

## Source excerpts

> Each Spark Job runs as an isolated Spark application with its own driver and (optionally) executors.

Source: https://iomete.com/resources/user-guide/spark-jobs/creating-spark-job

> Trigger type: Manual (default, run on demand), Interval (e.g. every 5 minutes), or Cron expression for recurring execution.

Source: https://iomete.com/resources/user-guide/spark-jobs/creating-spark-job

## Not stated in the documentation

- Nothing noted.
