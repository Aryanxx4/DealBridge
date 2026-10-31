---
type: Product Documentation Summary
title: "Jupyter notebooks"
description: "JupyterLab containers connected to compute clusters through Spark Connect."
resource: https://iomete.com/resources/user-guide/notebook/using-jupyterlab
tags: [iomete, platform]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/user-guide/notebook/using-jupyterlab
    title: "Using JupyterLab"
knowledge_id: iomete.platform.notebooks
category: platform
source_type: official
source_url: https://iomete.com/resources/user-guide/notebook/using-jupyterlab
source_document: "Using JupyterLab"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Jupyter notebooks

## Summary

IOMETE runs Jupyter containers whose JupyterLab interface opens from the console. Notebooks connect
to IOMETE compute clusters through Spark Connect, giving distributed Spark processing without a
local Spark instance. The Spark Connect session must be set up manually in each notebook.

## Details

- Open JupyterLab requires an Active container and VIEW permission.
- Containers include Git and AWS CLI tools.

## Source excerpts

> Jupyter Containers connect to IOMETE compute clusters through Spark Connect.

Source: https://iomete.com/resources/user-guide/notebook/using-jupyterlab

> There is no automatic Spark session configuration. You must set up the Spark Connect connection manually in each notebook.

Source: https://iomete.com/resources/user-guide/notebook/using-jupyterlab

## Not stated in the documentation

- Nothing noted.
