---
type: Product Documentation Summary
title: "Data masking policies"
description: "Dynamic column masking for sensitive data such as PII, PCI and PHI."
resource: https://iomete.com/resources/user-guide/data-security/data-masking
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/data-security/data-masking
    title: "Data Masking Policy"
knowledge_id: iomete.security.data-masking
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/data-security/data-masking
source_document: "Data Masking Policy"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Data masking policies

## Summary

IOMETE data masking policies mask or anonymize specific columns containing sensitive data
dynamically in query output. A masking policy targets one catalog, database, table and column and
applies to selected users or groups. Masking options include full masking, showing only the first or
last four characters, and hashing. Wildcards are not supported in masking policies.

## Details

- One column per policy; no wildcards.
- Special user entries {USER} (current user) and {OWNER} (table owner).
- Masking types include Mask, Mask Show Last 4, Mask Show First 4 and Mask Hash.

## Source excerpts

> IOMETE allows you to protect sensitive data using data masking. With this feature, you can create policies that mask or anonymize specific columns containing sensitive data, such as PII, PCI, and PHI, dynamically in the query output.

Source: https://iomete.com/resources/user-guide/data-security/data-masking

> Wildcard matching is not supported in data masking policy.

Source: https://iomete.com/resources/user-guide/data-security/data-masking

## Not stated in the documentation

- The page does not state that masking satisfies any specific regulation.
