---
type: Product Documentation Summary
title: "Personal access tokens"
description: "Calling the IOMETE API with personal access tokens."
resource: https://iomete.com/resources/user-guide/access-tokens/personal
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/access-tokens/personal
    title: "Personal Access Tokens"
knowledge_id: iomete.security.access-tokens
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/access-tokens/personal
source_document: "Personal Access Tokens"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Personal access tokens

## Summary

Personal access tokens let users call the IOMETE API from code or scripts instead of using a
password. Tokens are created under Settings, Access Tokens with an expiration, are shown only once,
and are sent in the X-API-Token header. Tokens can be suspended, renamed or deleted, and service
account tokens can cap request rates.

## Details

- Token prefix iomt_ for new tokens.
- Expiry notifications can be emailed.
- Service account tokens support request limits.

## Source excerpts

> Use a personal access token to call the IOMETE API from code or scripts, instead of your password.

Source: https://iomete.com/resources/user-guide/access-tokens/personal

> Send the token in the X-API-Token header.

Source: https://iomete.com/resources/user-guide/access-tokens/personal

## Not stated in the documentation

- Nothing noted.
