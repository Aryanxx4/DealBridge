"""G4 requirement intake: assessments, documents, requirements, revisions, change proposals

Revision ID: 0005_g4
Revises: 0004_g3
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0005_g4"
down_revision = "0004_g3"
branch_labels = None
depends_on = None

CATS = ["FUNCTIONAL_CAPABILITY", "DEPLOYMENT_INFRASTRUCTURE", "DATA_SOVEREIGNTY_RESIDENCY", "SECURITY_ACCESS_CONTROL", "INTEGRATION_COMPATIBILITY", "PERFORMANCE_SCALABILITY", "AVAILABILITY_RELIABILITY", "COMPLIANCE_GOVERNANCE", "COST_OPERATIONS", "OTHER"]
PRIOS = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NOT_SPECIFIED"]


def _in(col, vals):
    return f"{col} IN (" + ", ".join(f"'{v}'" for v in vals) + ")"


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _uuid(name, fk=None, nullable=True):
    return sa.Column(name, pg.UUID(as_uuid=True), *([sa.ForeignKey(fk)] if fk else []), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("owner_user_id", "users.id", False),
        _uuid("organization_id", "organizations.id", False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("context", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("intake_form", pg.JSONB),
        sa.Column("requirement_set_revision", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_req_seq", sa.Integer, nullable=False, server_default="1"),
        sa.Column("latest_version_no", sa.Integer, nullable=False, server_default="0"),
        *_ts(),
        sa.CheckConstraint(_in("status", ["DRAFT", "ANALYZING", "ANALYZED", "STALE"]), name="ck_assessments_status_enum"),
    )
    op.create_index("ix_assessments_owner_user_id", "assessments", ["owner_user_id"])
    op.create_index("ix_assessments_organization_id", "assessments", ["organization_id"])

    op.create_table(
        "uploaded_documents",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id"),
        _uuid("uploaded_by", "users.id", False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.Text, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pages", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("extraction_status", sa.String(20), nullable=False),
        sa.Column("extraction_message", sa.Text),
        *_ts(),
        sa.CheckConstraint(_in("kind", ["BUYER_PDF", "SELLER_DOC"]), name="ck_uploaded_documents_kind_enum"),
        sa.CheckConstraint(_in("extraction_status", ["OK", "SCANNED", "EMPTY", "MALFORMED"]), name="ck_uploaded_documents_extraction_status_enum"),
    )
    op.create_index("ix_uploaded_documents_assessment_id", "uploaded_documents", ["assessment_id"])
    op.create_index("ix_uploaded_documents_uploaded_by", "uploaded_documents", ["uploaded_by"])

    op.create_table(
        "requirements",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("display_id", sa.String(20), nullable=False),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("normalized_text", sa.Text, nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("priority_basis", sa.Text),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("source_reference", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("buyer_confirmed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("needs_clarification", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("clarifying_question", sa.Text),
        sa.Column("clarification_waived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_removed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("removed_at", sa.DateTime(timezone=True)),
        *_ts(),
        sa.UniqueConstraint("assessment_id", "seq", name="uq_requirements_assessment_seq"),
        sa.CheckConstraint(_in("category", CATS), name="ck_requirements_category_enum"),
        sa.CheckConstraint(_in("priority", PRIOS), name="ck_requirements_priority_enum"),
        sa.CheckConstraint(_in("source_type", ["PDF", "CHAT", "FORM", "MANUAL"]), name="ck_requirements_source_type_enum"),
    )
    op.create_index("ix_requirements_assessment_id", "requirements", ["assessment_id"])

    op.create_table(
        "requirement_revisions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("requirement_id", "requirements.id", False),
        sa.Column("revision_no", sa.Integer, nullable=False),
        sa.Column("change_type", sa.String(30), nullable=False),
        sa.Column("changes", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        _uuid("actor_user_id", "users.id"),
        sa.Column("actor_role", sa.String(20)),
        sa.Column("origin", sa.String(10), nullable=False),
        sa.Column("assessment_revision", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(_in("change_type", ["CREATED", "EDITED", "CONFIRMED", "CLARIFICATION_WAIVED", "REMOVED", "RESTORED"]), name="ck_requirement_revisions_change_type_enum"),
        sa.CheckConstraint(_in("origin", ["UI", "CHAT", "FORM", "PDF", "SYSTEM"]), name="ck_requirement_revisions_origin_enum"),
    )
    op.create_index("ix_requirement_revisions_requirement_id", "requirement_revisions", ["requirement_id"])
    op.create_index("ix_requirement_revisions_actor_user_id", "requirement_revisions", ["actor_user_id"])

    op.create_table(
        "change_proposals",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        _uuid("message_id", "messages.id"),
        sa.Column("ops", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("applied_op_indexes", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("result", pg.JSONB),
        *_ts(),
        sa.CheckConstraint(_in("status", ["PENDING", "APPLIED", "DISMISSED"]), name="ck_change_proposals_status_enum"),
    )
    op.create_index("ix_change_proposals_assessment_id", "change_proposals", ["assessment_id"])
    op.create_index("ix_change_proposals_message_id", "change_proposals", ["message_id"])

    # Foreign keys deferred from earlier gates (tables now exist).
    op.create_foreign_key("fk_jobs_assessment_id_assessments", "jobs", "assessments", ["assessment_id"], ["id"])
    op.create_foreign_key("fk_conversations_assessment_id_assessments", "conversations", "assessments", ["assessment_id"], ["id"])
    op.create_foreign_key("fk_conversations_requirement_id_requirements", "conversations", "requirements", ["requirement_id"], ["id"])
    op.create_foreign_key("fk_tickets_assessment_id_assessments", "tickets", "assessments", ["assessment_id"], ["id"])
    op.create_foreign_key("fk_tickets_requirement_id_requirements", "tickets", "requirements", ["requirement_id"], ["id"])


def downgrade() -> None:
    for name, table in (
        ("fk_tickets_requirement_id_requirements", "tickets"),
        ("fk_tickets_assessment_id_assessments", "tickets"),
        ("fk_conversations_requirement_id_requirements", "conversations"),
        ("fk_conversations_assessment_id_assessments", "conversations"),
        ("fk_jobs_assessment_id_assessments", "jobs"),
    ):
        op.drop_constraint(name, table, type_="foreignkey")
    for t in ("change_proposals", "requirement_revisions", "requirements", "uploaded_documents", "assessments"):
        op.drop_table(t)
