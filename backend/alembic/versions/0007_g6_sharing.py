"""G6 sharing and collaboration: assessment_shares, seller_responses, follow_up_requests, follow_up_messages

Revision ID: 0007_g6
Revises: 0006_g5
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0007_g6"
down_revision = "0006_g5"
branch_labels = None
depends_on = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _uuid(name, fk=None, nullable=True):
    return sa.Column(name, pg.UUID(as_uuid=True), *([sa.ForeignKey(fk)] if fk else []), nullable=nullable)


def _idx(table, *cols):
    for c in cols:
        op.create_index(f"ix_{table}_{c}", table, [c])


def upgrade() -> None:
    op.create_table(
        "assessment_shares",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        _uuid("seller_org_id", "organizations.id", False),
        _uuid("version_id", "assessment_versions.id", False),
        _uuid("shared_by", "users.id", False),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        _uuid("revoked_by", "users.id"),
        *_ts(),
    )
    _idx("assessment_shares", "assessment_id", "seller_org_id", "version_id", "shared_by", "revoked_by")

    op.create_table(
        "seller_responses",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        _uuid("requirement_id", "requirements.id", False),
        _uuid("version_id", "assessment_versions.id", False),
        _uuid("seller_user_id", "users.id", False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("assertion", sa.String(30), nullable=False),
        sa.Column("attachment_document_ids", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        *_ts(),
        sa.CheckConstraint("assertion IN ('NONE', 'CONFIRMS_SUPPORT', 'CONFIRMS_LIMITATION', 'NEEDS_INFO_FROM_BUYER')", name="ck_seller_responses_assertion_enum"),
    )
    _idx("seller_responses", "assessment_id", "requirement_id", "version_id", "seller_user_id")

    op.create_table(
        "follow_up_requests",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("assessment_id", "assessments.id", False),
        _uuid("seller_org_id", "organizations.id", False),
        _uuid("requested_by", "users.id", False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("related_requirement_ids", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("seller_decision", sa.String(20), nullable=False),
        sa.Column("decision_reason", sa.Text),
        _uuid("assigned_owner_user_id", "users.id"),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        _uuid("closed_by", "users.id"),
        *_ts(),
        sa.CheckConstraint("status IN ('REQUESTED', 'IN_PROGRESS', 'RESPONDED', 'CLOSED')", name="ck_follow_up_requests_status_enum"),
        sa.CheckConstraint("seller_decision IN ('PENDING', 'ACCEPTED', 'REJECTED')", name="ck_follow_up_requests_seller_decision_enum"),
    )
    _idx("follow_up_requests", "assessment_id", "seller_org_id", "requested_by", "assigned_owner_user_id", "closed_by")

    op.create_table(
        "follow_up_messages",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("follow_up_id", "follow_up_requests.id", False),
        _uuid("author_user_id", "users.id", False),
        sa.Column("author_role", sa.String(20), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("attachment_document_ids", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    _idx("follow_up_messages", "follow_up_id", "author_user_id")


def downgrade() -> None:
    for t in ("follow_up_messages", "follow_up_requests", "seller_responses", "assessment_shares"):
        op.drop_table(t)
