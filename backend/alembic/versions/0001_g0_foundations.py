"""G0 foundations: identity, jobs, audit, knowledge state, vector collections

Revision ID: 0001_g0
Revises:
Create Date: 2026-10-31
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0001_g0"
down_revision = None
branch_labels = None
depends_on = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _in(col, vals):
    return f"{col} IN (" + ", ".join(f"'{v}'" for v in vals) + ")"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        *_ts(),
        sa.CheckConstraint(_in("kind", ["BUYER_ORG", "SELLER_ORG", "INTERNAL"]), name="ck_organizations_kind_enum"),
    )
    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("organization_id", pg.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        *_ts(),
        sa.CheckConstraint(_in("role", ["BUYER", "SELLER", "ADMIN"]), name="ck_users_role_enum"),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.create_table(
        "jobs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("assessment_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("progress_done", sa.Integer, nullable=False, server_default="0"),
        sa.Column("progress_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("progress_message", sa.Text),
        sa.Column("result", pg.JSONB),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        *_ts(),
        sa.CheckConstraint(_in("type", ["EXTRACT_PDF", "ANALYZE", "REINDEX"]), name="ck_jobs_type_enum"),
        sa.CheckConstraint(_in("status", ["QUEUED", "RUNNING", "SUCCEEDED", "FAILED"]), name="ck_jobs_status_enum"),
    )
    op.create_index("ix_jobs_assessment_id", "jobs", ["assessment_id"])
    op.create_index("ix_jobs_created_by", "jobs", ["created_by"])

    op.create_table(
        "audit_events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", sa.String(20)),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("metadata", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])

    op.create_table(
        "knowledge_state",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("epoch", sa.Integer, nullable=False, server_default="0"),
        *_ts(),
    )
    op.execute("INSERT INTO knowledge_state (id, epoch) VALUES (1, 0)")

    op.create_table(
        "vector_collections",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("embedding_model", sa.String(200), nullable=False),
        sa.Column("dimension", sa.Integer, nullable=False),
        sa.Column("last_reindexed_at", sa.DateTime(timezone=True)),
        *_ts(),
    )


def downgrade() -> None:
    for t in ("vector_collections", "knowledge_state", "audit_events", "jobs", "users", "organizations"):
        op.drop_table(t)
