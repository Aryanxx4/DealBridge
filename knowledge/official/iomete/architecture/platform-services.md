---
type: Product Documentation Summary
title: "Platform services architecture"
description: "The microservices behind the IOMETE console and how traffic reaches them."
resource: https://iomete.com/resources/getting-started/architecture
tags: [iomete, architecture]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/getting-started/architecture
    title: "IOMETE Architecture: Control Plane, Data Planes, Kubernetes"
knowledge_id: iomete.architecture.services
category: architecture
source_type: official
source_url: https://iomete.com/resources/getting-started/architecture
source_document: "IOMETE Architecture: Control Plane, Data Planes, Kubernetes"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Platform services architecture

## Summary

IOMETE deploys as a Helm chart into a Kubernetes cluster and uses object storage as its data layer,
keeping metadata in PostgreSQL. The console is backed by independent microservices: a Gateway (Nginx
reverse proxy), Core, Cluster, Identity, SQL, Catalog, Iceberg REST Catalog and Health Check
services. Spark workloads are created on demand by a Spark Operator.

## Details

- Three tiers: infrastructure (Kubernetes, object storage), platform services, workloads.
- Gateway routes API, UI, Spark Connect, Arrow Flight and WebSocket traffic.
- Identity Service handles users, groups, roles, LDAP/SAML/OIDC and Apache Ranger policies.
- Iceberg REST Catalog enforces Apache Ranger policies on every data request.
- Health checks run every 10 seconds with 48 hours of history.

## Source excerpts

> IOMETE runs on Kubernetes (any cloud provider or on-premises data center), stores data in object storage, and keeps metadata in PostgreSQL.

Source: https://iomete.com/resources/getting-started/architecture

> All traffic enters the platform through a single Nginx reverse proxy.

Source: https://iomete.com/resources/getting-started/architecture

> Every data request passes through Apache Ranger policy enforcement, so access control stays consistent no matter how data is queried.

Source: https://iomete.com/resources/getting-started/architecture

## Not stated in the documentation

- Nothing noted.
