---
type: Product Documentation Summary
title: "On-premises installation on Kubernetes"
description: "Prerequisites and steps for installing the IOMETE data plane on-premises with Helm."
resource: https://iomete.com/resources/deployment/on-prem/install
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/on-prem/install
    title: "On-Premises Deployment Guide"
knowledge_id: iomete.deployment.on-premises
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/on-prem/install
source_document: "On-Premises Deployment Guide"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# On-premises installation on Kubernetes

## Summary

IOMETE is installed on-premises into a Kubernetes cluster using a Helm chart (iomete-data-plane-
enterprise). Before installing, a team needs a Kubernetes cluster with capacity for IOMETE services
and Spark workloads, an object store, a PostgreSQL database for metadata, Istio for UI access, and
the kubectl and helm tools. A Terraform option is mentioned for Azure, and a dedicated guide exists
for Nutanix Kubernetes Platform.

## Details

- IOMETE services need at least 12 CPU cores and 24GB RAM; Spark workloads need at least one node with 4 CPU cores and 32GB RAM.
- Object storage options listed: Apache Ozone, Dell ECS, IBM Cloud Object Storage, MinIO or other S3-compatible storage, AWS S3, Azure Blob Storage, Google Cloud Storage.
- A PostgreSQL database is required for IOMETE metadata.
- Installation adds the IOMETE Helm repository and runs helm upgrade --install for the data plane chart.
- Cluster-level resources (service account, Spark Operator CRDs, webhook) can be created by Helm or by a Kubernetes administrator.

## Source excerpts

> This guide provides detailed instructions for deploying IOMETE on-premises within a Kubernetes environment, ensuring you have a seamless setup process.

Source: https://iomete.com/resources/deployment/on-prem/install

> IOMETE services: at least 12 CPU cores and 24GB of RAM. This includes headroom for Kubernetes system pods and Istio.

Source: https://iomete.com/resources/deployment/on-prem/install

> Spark workloads: at least one node with 4 CPU cores and 32GB of RAM for Spark drivers and executors.

Source: https://iomete.com/resources/deployment/on-prem/install

> PostgreSQL database for IOMETE metadata.

Source: https://iomete.com/resources/deployment/on-prem/install

## Not stated in the documentation

- Installation without internet access (offline image registries) is not described on this page.
