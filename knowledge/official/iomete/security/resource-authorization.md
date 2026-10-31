---
type: Product Documentation Summary
title: "Domain authorization and resource permissions"
description: "Granular per-resource permissions with the Resource Authorization System."
resource: https://iomete.com/resources/user-guide/iam/ras/domain-authorization
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/iam/ras/domain-authorization
    title: "Domain Authorization"
knowledge_id: iomete.security.resource-authorization
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/iam/ras/domain-authorization
source_document: "Domain Authorization"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Domain authorization and resource permissions

## Summary

Domain Authorization moves domain security from role mapping to granular permissions granted
directly to users or groups. With the feature enabled, no default permissions are assigned when
someone joins a domain, and domains can be owned by a user or a group. It is controlled by a feature
flag available from version 3.16.x.

## Details

- Feature flag: domainLevelBundleAuthorization.
- Zero-trust default: all access must be granted explicitly.
- Example granular permissions: Create Compute, Manage Spark Settings.

## Source excerpts

> When this feature is enabled, no default permissions are assigned to users or groups upon joining a domain.

Source: https://iomete.com/resources/user-guide/iam/ras/domain-authorization

> A domain can now be owned by a User or a Group.

Source: https://iomete.com/resources/user-guide/iam/ras/domain-authorization

## Not stated in the documentation

- Nothing noted.
