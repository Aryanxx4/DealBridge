---
type: Product Documentation Summary
title: "LDAP and Active Directory integration"
description: "Connecting IOMETE to an LDAP or Active Directory directory to import users and groups."
resource: https://iomete.com/resources/user-guide/ldap-configuration
tags: [iomete, security]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/ldap-configuration
    title: "LDAP Configuration"
knowledge_id: iomete.security.ldap
category: security
source_type: official
source_url: https://iomete.com/resources/user-guide/ldap-configuration
source_document: "LDAP Configuration"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# LDAP and Active Directory integration

## Summary

Organizations that manage users in LDAP or Active Directory can connect IOMETE to the directory to
import users and groups and let LDAP users sign in with existing credentials. Configuration is done
under Settings, IAM, LDAP by users with the IAM Manager admin role. Each installation supports a
single platform-wide LDAP configuration.

## Details

- Settings include connection URL, bind DN and bind credential, with connection and authentication tests.
- User attribute mappings map username, email, first and last name to LDAP attributes.
- One LDAP configuration per installation, shared across workspaces and clusters.

## Source excerpts

> If your organization already manages users in LDAP or Active Directory, you can connect IOMETE to that directory to import users and groups and let LDAP users sign in with their existing credentials.

Source: https://iomete.com/resources/user-guide/ldap-configuration

> Each IOMETE installation supports a single, platform-wide LDAP configuration.

Source: https://iomete.com/resources/user-guide/ldap-configuration

## Not stated in the documentation

- Nothing noted.
