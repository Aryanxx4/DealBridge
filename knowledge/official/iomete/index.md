---
okf_version: "0.2"
---

# IOMETE official product knowledge

Curated from the official IOMETE documentation (https://iomete.com/resources/). Each concept records its source page, its knowledge_id and its approval status.


# Architecture

* [Apache Iceberg tables](architecture/apache-iceberg.md) - `iomete.architecture.iceberg`: How IOMETE uses Apache Iceberg as its default table format.
* [Compute clusters](architecture/compute-clusters.md) - `iomete.architecture.compute-clusters`: Spark-based compute clusters that serve SQL queries over shared object storage.
* [Lakehouse platform overview](architecture/lakehouse-overview.md) - `iomete.architecture.lakehouse`: What IOMETE is and how its decoupled compute and storage architecture works.
* [Platform services architecture](architecture/platform-services.md) - `iomete.architecture.services`: The microservices behind the IOMETE console and how traffic reaches them.
* [Scalability](architecture/scalability.md) - `iomete.architecture.scalability`: How IOMETE scales across infrastructure, platform services, compute and storage.
* [Storage backends](architecture/storage-backends.md) - `iomete.architecture.storage`: Object storage systems IOMETE supports as its data layer.
* [Time travel on Iceberg tables](architecture/time-travel.md) - `iomete.architecture.time-travel`: Querying historical table snapshots in IOMETE.

# Deployment

* [Supported infrastructure providers](deployment/cloud-providers.md) - `iomete.deployment.cloud-providers`: Cloud providers and on-premises Kubernetes supported by the IOMETE Helm deployment.
* [Deployment options and data residency](deployment/deployment-options.md) - `iomete.deployment.options`: Where IOMETE can be deployed and where customer data stays, per the IOMETE overview page.
* [Kubernetes requirement](deployment/kubernetes.md) - `iomete.deployment.kubernetes`: IOMETE requires a Kubernetes cluster; k3s is suggested for demos and proofs of concept.
* [Metadata database](deployment/metadata-database.md) - `iomete.deployment.metadata-database`: The relational database IOMETE uses for platform and data lake metadata.
* [Multi-cluster deployments](deployment/multi-cluster.md) - `iomete.deployment.multi-cluster`: Deployment models: single installation, independent installations, and multi-cluster with a shared global database.
* [Kubernetes network policies](deployment/network-policies.md) - `iomete.deployment.network-policies`: Network policies IOMETE needs inside the Kubernetes cluster.
* [On-premises installation on Kubernetes](deployment/on-premises-installation.md) - `iomete.deployment.on-premises`: Prerequisites and steps for installing the IOMETE data plane on-premises with Helm.
* [Secrets, logging and monitoring configuration](deployment/operations-configuration.md) - `iomete.deployment.operations`: Where IOMETE stores secrets and which logging and monitoring back ends it can use.

# Integrations

* [Apache Airflow plugin](integrations/airflow.md) - `iomete.integrations.airflow`: Triggering and managing IOMETE Spark jobs from Airflow DAGs.
* [Apache Superset connection](integrations/apache-superset.md) - `iomete.integrations.superset`: Connecting Apache Superset to IOMETE.
* [dbt adapter](integrations/dbt.md) - `iomete.integrations.dbt`: Running dbt SQL transformations on IOMETE with the dbt-iomete adapter.
* [Third-party ecosystem integrations](integrations/ecosystem.md) - `iomete.integrations.ecosystem`: Third-party governance, observability, analytics and storage tools listed by IOMETE.
* [Git integration for SQL worksheets](integrations/git.md) - `iomete.integrations.git`: Hosting SQL worksheets in Git repositories (GitLab).
* [Migrating tables from JDBC sources](integrations/jdbc-migration.md) - `iomete.integrations.jdbc-migration`: Tutorial for copying tables from JDBC databases into IOMETE.
* [Metabase connection](integrations/metabase.md) - `iomete.integrations.metabase`: Connecting Metabase to an IOMETE compute cluster.
* [Power BI connection](integrations/power-bi.md) - `iomete.integrations.power-bi`: Connection methods for Microsoft Power BI.
* [Query federation](integrations/query-federation.md) - `iomete.integrations.query-federation`: Joining data from JDBC databases, files and Snowflake in one SQL query.
* [SQL clients and JDBC drivers](integrations/sql-clients-jdbc.md) - `iomete.integrations.sql-clients`: Connecting SQL clients such as DBeaver over Arrow Flight SQL JDBC.
* [Tableau connection](integrations/tableau.md) - `iomete.integrations.tableau`: Connection methods for Tableau.

# Platform

* [Data Catalog](platform/data-catalog.md) - `iomete.platform.data-catalog`: Searching, browsing and tagging tables in the IOMETE Data Catalog.
* [Job Orchestrator](platform/job-orchestrator.md) - `iomete.platform.job-orchestrator`: Priority-based, resource-aware scheduling of Spark jobs.
* [Jupyter notebooks](platform/jupyter-notebooks.md) - `iomete.platform.notebooks`: JupyterLab containers connected to compute clusters through Spark Connect.
* [Monitoring](platform/monitoring.md) - `iomete.platform.monitoring`: Admin monitoring surfaces: health, namespace quotas, query monitoring, search engine and Grafana links.
* [Spark catalogs](platform/spark-catalogs.md) - `iomete.platform.spark-catalogs`: Managed Iceberg REST catalogs and external catalogs in IOMETE.
* [Spark jobs and scheduling](platform/spark-jobs.md) - `iomete.platform.spark-jobs`: Running batch Spark jobs in IOMETE with schedules and resource bundles.
* [SQL Editor](platform/sql-editor.md) - `iomete.platform.sql-editor`: The browser-based SQL environment with collaboration, Git and dashboards.
* [Streaming jobs](platform/streaming-jobs.md) - `iomete.platform.streaming`: Long-running Spark applications for continuous data processing.
* [Automated table maintenance](platform/table-maintenance.md) - `iomete.platform.table-maintenance`: Background maintenance of Iceberg tables (compaction, snapshots, orphan files).

# Security

* [Personal access tokens](security/access-tokens.md) - `iomete.security.access-tokens`: Calling the IOMETE API with personal access tokens.
* [Authentication and single sign-on](security/authentication-sso.md) - `iomete.security.authentication`: Authentication modes supported by the IOMETE Identity Service, including SSO.
* [Data access policies (database, table and column)](security/data-access-policies.md) - `iomete.security.access-policies`: Resource-based access policies that grant or deny access to databases, tables and columns.
* [Data masking policies](security/data-masking.md) - `iomete.security.data-masking`: Dynamic column masking for sensitive data such as PII, PCI and PHI.
* [LDAP and Active Directory integration](security/ldap.md) - `iomete.security.ldap`: Connecting IOMETE to an LDAP or Active Directory directory to import users and groups.
* [Domain authorization and resource permissions](security/resource-authorization.md) - `iomete.security.resource-authorization`: Granular per-resource permissions with the Resource Authorization System.
* [Row-level filter policies](security/row-level-filter.md) - `iomete.security.row-level-filter`: Restricting which table rows a user or group can see.
* [Security layers](security/security-layers.md) - `iomete.security.overview`: The four layers of IOMETE security: network policies, identity, resource access and data security.
* [Tag-based policies and data classifications](security/tag-based-policies.md) - `iomete.security.tag-based`: Access and masking policies driven by classification tags such as PII.
