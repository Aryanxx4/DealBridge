---
type: Product Documentation Summary
title: "Security layers"
description: "The four layers of IOMETE security: network policies, identity, resource access and data security."
resource: https://iomete.com/resources/user-guide/security-overview
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/security-overview
    title: "Security Overview"
knowledge_id: iomete.security.overview
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/security-overview
source_document: "Security Overview"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Security layers

## Summary

IOMETE organizes security into four layers: infrastructure (Kubernetes network policies), identity
(IAM), resource access (Resource Access Service bundles) and data (data security policies). A Spark
query request passes through all four layers in order, and a failure at any layer blocks it.

## Details

- Layer 1 Network Policies: can components reach each other inside the cluster?
- Layer 2 IAM: who is the user and how did they authenticate?
- Layer 3 RAS resource bundles: which compute clusters, Spark jobs and workspaces can the user operate?
- Layer 4 Data Security: which databases, tables, columns and rows can the user query?
- Platform roles such as IAM_MANAGER and DATA_SECURITY_AND_AUDIT_MANAGER grant admin rights.

## Source excerpts

> IOMETE security is organized into four complementary layers.

Source: https://iomete.com/resources/user-guide/security-overview

> A request to run a Spark query passes through all four layers in order. A failure at any layer blocks the request regardless of what the other layers permit.

Source: https://iomete.com/resources/user-guide/security-overview

## Not stated in the documentation

- Compliance certifications (for example SOC 2 or ISO 27001) are not mentioned on this page.
