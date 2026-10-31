---
type: Product Documentation Summary
title: "Authentication and single sign-on"
description: "Authentication modes supported by the IOMETE Identity Service, including SSO."
resource: https://iomete.com/resources/user-guide/security-overview
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/security-overview
    title: "Security Overview"
knowledge_id: iomete.security.authentication
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/security-overview
source_document: "Security Overview"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Authentication and single sign-on

## Summary

The IOMETE security overview lists authentication via local credentials, LDAP directory sync, or
federated identity through SAML or OIDC, naming Okta, OneLogin, Microsoft Entra ID and SCIM
provisioning. Users can be person accounts or service accounts, and groups (which can be nested) are
the main unit of permission management.

## Details

- Authentication: local credentials, LDAP sync, SAML/OIDC federation.
- Identity providers named: Okta, OneLogin, Microsoft Entra ID; SCIM provisioning mentioned.
- Groups can be nested and are used across all other security layers.

## Source excerpts

> Authentication — local credentials, LDAP directory sync, or federated identity via SAML/OIDC (Okta, OneLogin, Microsoft Entra ID, SCIM provisioning).

Source: https://iomete.com/resources/user-guide/security-overview

> Groups — named collections of users; groups can be nested.

Source: https://iomete.com/resources/user-guide/security-overview

## Not stated in the documentation

- Multi-factor authentication is not described on this page.
