---
type: Product Documentation Summary
title: "Scalability"
description: "How IOMETE scales across infrastructure, platform services, compute and storage."
resource: https://iomete.com/resources/getting-started/scalability
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/getting-started/scalability
    title: "Scalability"
knowledge_id: iomete.architecture.scalability
category: architecture
source_type: official
source_url: https://iomete.com/resources/getting-started/scalability
source_document: "Scalability"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Scalability

## Summary

IOMETE is built on Kubernetes, Apache Spark and Apache Iceberg and scales at four independent
layers: infrastructure, platform services, compute clusters and storage. Capacity can be added by
adding Kubernetes worker nodes manually or through cloud autoscalers, and platform services can use
Horizontal Pod Autoscaling.

## Details

- Cloud autoscalers mentioned: AWS Karpenter, GKE Node Auto-Provisioning, AKS Cluster Autoscaler.
- On-premises: scale the node pool manually or with infrastructure automation.
- HPA is disabled by default for most platform services.

## Source excerpts

> IOMETE scales at four independent layers: infrastructure, platform services, compute clusters, and storage.

Source: https://iomete.com/resources/getting-started/scalability

> Horizontal Pod Autoscaling (HPA) lets individual services scale their replica count based on CPU or memory utilization.

Source: https://iomete.com/resources/getting-started/scalability

## Not stated in the documentation

- No benchmark numbers or maximum data volumes are stated on this page.
