"""G5 assessment engine: assessment_versions, requirement_assessments, evidence_references

Revision ID: 0006_g5
Revises: 0005_g4
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0006_g5"
down_revision = "0005_g4"
branch_labels = None
depends_on = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _uuid(name, fk=None, nullable=True):
    return sa.Column(name, pg.UUID(as_uuid=True), *([sa.ForeignKey(fk)] if fk else []), nullable=nullable)


def _j(name, default="'[]'::jsonb"):
    return sa.Column(name, pg.JSONB, nullable=False, server_default=sa.text(default))


def upgrade() -> None:
    op.create_table(
        "assessment_versions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        sa.Column("version_no", sa.Integer, nullable=False),
        sa.Column("requirement_set_revision", sa.Integer, nullable=False),
        _j("requirements_snapshot"),
        sa.Column("knowledge_epoch", sa.Integer, nullable=False),
        _j("summary", "'{}'::jsonb"),
        sa.Column("model", sa.String(100)),
        _j("prompt_versions", "'{}'::jsonb"),
        _uuid("job_id", "jobs.id"),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        *_ts(),
        sa.UniqueConstraint("assessment_id", "version_no", name="uq_assessment_versions_assessment_version"),
    )
    op.create_index("ix_assessment_versions_assessment_id", "assessment_versions", ["assessment_id"])
    op.create_index("ix_assessment_versions_job_id", "assessment_versions", ["job_id"])

    op.create_table(
        "requirement_assessments",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("version_id", "assessment_versions.id", False),
        _uuid("requirement_id", "requirements.id", False),
        sa.Column("display_id", sa.String(20), nullable=False),
        sa.Column("requirement_text", sa.Text, nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        _j("explanation", "'{}'::jsonb"),
        sa.Column("supported_part", sa.Text),
        sa.Column("unestablished_part", sa.Text),
        _j("assumptions"),
        _j("missing_information"),
        _j("questions_for_seller"),
        sa.Column("has_conflict", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("conflict_description", sa.Text),
        sa.Column("is_blocker", sa.Boolean, nullable=False, server_default=sa.false()),
        _j("guardrail_notes"),
        _j("retrieval_summary", "'{}'::jsonb"),
        sa.Column("model", sa.String(100)),
        sa.Column("prompt_version", sa.String(50)),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        *_ts(),
        sa.UniqueConstraint("version_id", "requirement_id", name="uq_requirement_assessments_version_requirement"),
        sa.CheckConstraint("status IN ('SUPPORTED', 'PARTIALLY_SUPPORTED', 'NEEDS_VALIDATION', 'NOT_SUPPORTED', 'UNKNOWN')", name="ck_requirement_assessments_status_enum"),
    )
    op.create_index("ix_requirement_assessments_version_id", "requirement_assessments", ["version_id"])
    op.create_index("ix_requirement_assessments_requirement_id", "requirement_assessments", ["requirement_id"])

    op.create_table(
        "evidence_references",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("requirement_assessment_id", "requirement_assessments.id", False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("collection", sa.String(20), nullable=False),
        sa.Column("knowledge_id", sa.String(200), nullable=False),
        sa.Column("chunk_id", sa.String(100), nullable=False),
        sa.Column("source_title", sa.Text, nullable=False),
        sa.Column("heading_path", sa.Text),
        sa.Column("source_url", sa.Text),
        sa.Column("source_document", sa.Text),
        sa.Column("source_label", sa.String(40), nullable=False),
        sa.Column("excerpt", sa.Text, nullable=False),
        sa.Column("knowledge_version", sa.Integer),
        sa.Column("last_verified_at", sa.String(40)),
        sa.Column("relevance_score", sa.Float),
        *_ts(),
        sa.CheckConstraint("collection IN ('OFFICIAL', 'RESOLVED')", name="ck_evidence_references_collection_enum"),
        sa.CheckConstraint("role IN ('SUPPORTS', 'LIMITS', 'RELATED')", name="ck_evidence_references_role_enum"),
    )
    op.create_index("ix_evidence_references_requirement_assessment_id", "evidence_references", ["requirement_assessment_id"])


def downgrade() -> None:
    for t in ("evidence_references", "requirement_assessments", "assessment_versions"):
        op.drop_table(t)
