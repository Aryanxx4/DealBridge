---
type: Product Documentation Summary
title: "Kubernetes network policies"
description: "Network policies IOMETE needs inside the Kubernetes cluster."
resource: https://iomete.com/resources/deployment/network-policies
tags: [iomete, deployment]
status: stable
generated: { by: dealbridge-curation/1.0, at: 2026-10-31T18:00:00Z }
verified: { by: process:dealbridge-excerpt-check, at: 2026-10-31T18:02:41Z }
sources:
  - id: doc
    resource: https://iomete.com/resources/deployment/network-policies
    title: "Kubernetes Network Policies"
knowledge_id: iomete.deployment.network-policies
category: deployment
source_type: official
source_url: https://iomete.com/resources/deployment/network-policies
source_document: "Kubernetes Network Policies"
last_verified_at: 2026-10-31
version: 1
approval_status: approved
---

# Kubernetes network policies

## Summary

IOMETE relies on Kubernetes NetworkPolicy resources. The documentation describes a policy that lets
the Kubernetes API server reach the Spark Operator webhook, and a policy that allows IOMETE control
plane and data plane services to communicate across namespaces using the iomete.com/managed label.

## Details

- Spark Operator webhook policy: allows ingress from the API server IP to the webhook.
- Namespaces communication policy: uses the label iomete.com/managed: "true".
- Restrictive network policies can cause resource creation to time out.

## Source excerpts

> IOMETE services rely on specific network configurations to function properly in a Kubernetes cluster.

Source: https://iomete.com/resources/deployment/network-policies

> Kubernetes API server requires access to the Spark Operator webhook service.

Source: https://iomete.com/resources/deployment/network-policies

## Not stated in the documentation

- Nothing noted.
