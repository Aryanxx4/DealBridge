---
type: Product Documentation Summary
title: "Supported infrastructure providers"
description: "Cloud providers and on-premises Kubernetes supported by the IOMETE Helm deployment."
resource: https://iomete.com/resources/deployment/architecture-deployment
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/architecture-deployment
    title: "Deployment Architecture"
knowledge_id: iomete.deployment.cloud-providers
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/architecture-deployment
source_document: "Deployment Architecture"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Supported infrastructure providers

## Summary

The deployment architecture reference states that IOMETE runs on AWS, Azure, GCP and on-premises
Kubernetes. Provider differences are mainly the scratch directory path and whether zone-aware
scheduling is used. Everything ships as a single Helm chart that deploys the platform services into
one Kubernetes namespace.

## Details

- Providers: AWS, Azure, GCP and on-premises Kubernetes.
- Zone-aware scheduling is listed only for AWS.
- Single Helm chart: iomete-data-plane-enterprise.
- Spark pods include tolerations for dedicated nodes and ARM64 architecture.

## Source excerpts

> IOMETE runs on AWS, Azure, GCP, and on-premises Kubernetes.

Source: https://iomete.com/resources/deployment/architecture-deployment

> Everything ships as a single Helm chart (iomete-data-plane-enterprise), which deploys all platform services into one Kubernetes namespace.

Source: https://iomete.com/resources/deployment/architecture-deployment

## Not stated in the documentation

- Managed SaaS hosting by the vendor is not described on this page.
