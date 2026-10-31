# Knowledge gaps

These topics, which buyers commonly ask about, are **not established** by the official IOMETE documentation pages fetched on 2026-10-31. DealBridge must answer them as Unknown or Needs validation, or route them to the product team. They must never be filled in from memory (R8).

| Topic | Status | Notes |
|---|---|---|
| Air-gapped / fully offline installation | Not found in fetched docs | The overview names on-premises, cloud and hybrid deployment. No fetched page describes an air-gapped install, offline image registries or operation without internet access. |
| Compliance certifications (SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, FedRAMP, ...) | Not found | No fetched page names a certification. The masking page mentions PII, PCI and PHI only as *kinds of sensitive data*, not as certifications. |
| Encryption at rest | Not found | The overview lists "encryption" generically among security features. Only PostgreSQL SSL and TrustStore configuration are described specifically. |
| Pricing and licensing | Not covered | Out of scope for product documentation. |
| Migration effort estimates | Not covered | A JDBC migration tutorial exists, but no effort estimates or migration services are described. |
| Multi-factor authentication | Not found | SSO via SAML/OIDC is documented. MFA itself is not described. |
| Data lineage inside IOMETE | Partial | Lineage is mentioned only via the third-party OpenMetadata integration. |
| Supported Kubernetes versions | Not found on the fetched pages | |
| Performance benchmarks / maximum scale | Not found | The scalability page describes mechanisms, not numbers. |
| Customer-specific internal standards (for example FinBank FBS-114) | Cannot be documented | These are buyer-specific and need vendor validation. |

## Coverage by category (44 approved concepts)
- deployment: 8
- architecture: 7
- security: 9
- platform: 9
- integrations: 11

The build prompt asked for a `concepts` category only where the official documentation itself explains a concept. The lakehouse explanation lives in `architecture/lakehouse-overview.md`, because the overview page explains it in IOMETE's own terms. Generic educational explanations are generated at answer time and labelled as general.
