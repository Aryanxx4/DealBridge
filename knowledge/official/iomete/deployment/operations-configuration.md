---
type: Product Documentation Summary
title: "Secrets, logging and monitoring configuration"
description: "Where IOMETE stores secrets and which logging and monitoring back ends it can use."
resource: https://iomete.com/resources/deployment/architecture-deployment
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/architecture-deployment
    title: "Deployment Architecture"
knowledge_id: iomete.deployment.operations
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/architecture-deployment
source_document: "Deployment Architecture"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Secrets, logging and monitoring configuration

## Summary

The deployment reference describes configurable secret stores (Kubernetes Secrets by default,
encrypted in the IOMETE database, or HashiCorp Vault), log back ends (Kubernetes API by default,
Grafana Loki, Elasticsearch, Splunk) and Prometheus scraping when monitoring is enabled. PostgreSQL
SSL is optional, and self-signed certificates are handled by mounting a Java TrustStore.

## Details

- Secret store types: kubernetes (default), database (encrypted), vault.
- Logging back ends: kubernetes (default), loki, elasticsearch, splunk.
- Monitoring: set monitoring.enabled to add Prometheus scrape annotations.
- PostgreSQL SSL optional; when enabled JDBC uses sslmode=verify-full.

## Source excerpts

> You can choose where IOMETE keeps sensitive values like database passwords and API keys:

Source: https://iomete.com/resources/deployment/architecture-deployment

> If you run Prometheus, set monitoring.enabled to true.

Source: https://iomete.com/resources/deployment/architecture-deployment

> PostgreSQL SSL is optional. When ssl.enabled is true, JDBC connections use sslmode=verify-full.

Source: https://iomete.com/resources/deployment/architecture-deployment

## Not stated in the documentation

- Encryption at rest of object storage data is not described on this page.
