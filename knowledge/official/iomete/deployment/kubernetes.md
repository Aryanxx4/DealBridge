---
type: Product Documentation Summary
title: "Kubernetes requirement"
description: "IOMETE requires a Kubernetes cluster; k3s is suggested for demos and proofs of concept."
resource: https://iomete.com/resources/deployment/kubernetes
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/kubernetes
    title: "Kubernetes Setup Guide"
knowledge_id: iomete.deployment.kubernetes
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/kubernetes
source_document: "Kubernetes Setup Guide"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Kubernetes requirement

## Summary

IOMETE runs on Kubernetes. For production, the documentation recommends using the company's existing
production-ready Kubernetes cluster. For demos, proofs of concept, development and small non-
critical workloads, it recommends k3s and shows a single-node installation.

## Details

- Production: use an existing production-ready Kubernetes cluster.
- k3s is recommended for demos and POCs, development and testing, and small non-critical production workloads.
- The guide warns to set firewall rules before installing k3s.

## Source excerpts

> IOMETE requires a Kubernetes cluster to run. For production environments, use your company's existing production-ready Kubernetes cluster.

Source: https://iomete.com/resources/deployment/kubernetes

> Demos and POCs - Quick setup for evaluations

Source: https://iomete.com/resources/deployment/kubernetes

## Not stated in the documentation

- Supported Kubernetes versions are not listed on this page.
