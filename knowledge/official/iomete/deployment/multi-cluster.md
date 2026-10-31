---
type: Product Documentation Summary
title: "Multi-cluster deployments"
description: "Deployment models: single installation, independent installations, and multi-cluster with a shared global database."
resource: https://iomete.com/resources/deployment/multi-cluster-setup
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/multi-cluster-setup
    title: "Multi-Cluster Setup"
knowledge_id: iomete.deployment.multi-cluster
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/multi-cluster-setup
source_document: "Multi-Cluster Setup"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Multi-cluster deployments

## Summary

From version 3.16.x, IOMETE supports multi-cluster deployments in which several instances, each in
its own Kubernetes cluster, share common resources such as users, catalogs and domains through a
shared global database. The documentation notes a current limitation: there is no unified control
plane or single view across instances, and each instance is operated independently.

## Details

- Three deployment models: single installation; multiple independent installations; multi-cluster with shared global database.
- Independent installations have no shared state and are used for separate business units, regions or environments.
- A true single control plane is described as planned for a future release.

## Source excerpts

> Starting from version 3.16.x, IOMETE supports multi-cluster deployments.

Source: https://iomete.com/resources/deployment/multi-cluster-setup

> This implementation does not provide a unified control plane or a single view across instances.

Source: https://iomete.com/resources/deployment/multi-cluster-setup

> Each instance is managed separately, and there is no synchronization between them.

Source: https://iomete.com/resources/deployment/multi-cluster-setup

## Not stated in the documentation

- Nothing noted.
