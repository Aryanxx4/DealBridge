---
type: Product Documentation Summary
title: "Apache Airflow plugin"
description: "Triggering and managing IOMETE Spark jobs from Airflow DAGs."
resource: https://iomete.com/resources/integrations/airflow/getting-started
tags: [iomete, integrations]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/integrations/airflow/getting-started
    title: "Getting Started with Airflow"
knowledge_id: iomete.integrations.airflow
category: integrations
source_type: official
source_url: https://iomete.com/resources/integrations/airflow/getting-started
source_document: "Getting Started with Airflow"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Apache Airflow plugin

## Summary

The IOMETE Airflow Plugin lets Airflow DAGs trigger and manage IOMETE Spark jobs. It submits each
job run, monitors status and cancels the run if the Airflow task is killed. It is installed with pip
(iomete-airflow-plugin) and requires Python 3.10 to 3.13 and Airflow 2.10.5 or later, below 4.0.

## Details

- Package: iomete-airflow-plugin.
- Works with Docker Compose or Helm-installed Airflow.

## Source excerpts

> The IOMETE Airflow Plugin lets you trigger and manage IOMETE Spark jobs from an Airflow DAG.

Source: https://iomete.com/resources/integrations/airflow/getting-started

> Apache Airflow >=2.10.5,<4.0.0

Source: https://iomete.com/resources/integrations/airflow/getting-started

## Not stated in the documentation

- Nothing noted.
