---
type: Product Documentation Summary
title: "SQL clients and JDBC drivers"
description: "Connecting SQL clients such as DBeaver over Arrow Flight SQL JDBC."
resource: https://iomete.com/resources/integrations/dbtools/dbeaver
tags: [iomete, integrations]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/integrations/dbtools/dbeaver
    title: "DBeaver"
knowledge_id: iomete.integrations.sql-clients
category: integrations
source_type: official
source_url: https://iomete.com/resources/integrations/dbtools/dbeaver
source_document: "DBeaver"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# SQL clients and JDBC drivers

## Summary

DBeaver connects to IOMETE over the Arrow Flight SQL protocol using a JDBC driver, either the IOMETE
custom build or the standard Apache Arrow Flight SQL JDBC driver. A legacy Hive JDBC driver over the
deprecated HiveServer2 protocol also exists but is slower and has known compatibility issues.

## Details

- IOMETE custom build adds proxy support, query timeout and named parameters.
- Use Arrow Flight SQL unless there is a specific reason to use the Hive driver.

## Source excerpts

> It connects to IOMETE over the Arrow Flight SQL protocol using a JDBC driver.

Source: https://iomete.com/resources/integrations/dbtools/dbeaver

> There's also a legacy Hive JDBC driver that connects over the deprecated HiveServer2 protocol.

Source: https://iomete.com/resources/integrations/dbtools/dbeaver

## Not stated in the documentation

- Nothing noted.
