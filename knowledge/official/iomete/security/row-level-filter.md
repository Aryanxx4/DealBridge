---
type: Product Documentation Summary
title: "Row-level filter policies"
description: "Restricting which table rows a user or group can see."
resource: https://iomete.com/resources/user-guide/data-security/row-level-filter
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/data-security/row-level-filter
    title: "Data Row Level Filter"
knowledge_id: iomete.security.row-level-filter
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/data-security/row-level-filter
source_document: "Data Row Level Filter"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Row-level filter policies

## Summary

Row-level filter policies let users access only a subset of rows in a table. A policy targets one
database and table, applies to users or groups, and uses a WHERE-clause filter expression. Filters
are evaluated in the order listed. Select is the only access type, and wildcards are not supported.

## Details

- One database and one table per policy.
- Filters are evaluated top to bottom.
- Leaving the filter empty grants select access without row restrictions.

## Source excerpts

> IOMETE Row-level Filter policies allow users to access only a subset of data based on the context in which they interact with the data.

Source: https://iomete.com/resources/user-guide/data-security/row-level-filter

> Wildcard matching is not supported in row level filter policy.

Source: https://iomete.com/resources/user-guide/data-security/row-level-filter

## Not stated in the documentation

- Nothing noted.
