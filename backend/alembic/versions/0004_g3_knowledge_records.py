"""G3 knowledge records (approved expert resolutions)

Revision ID: 0004_g3
Revises: 0003_g2
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0004_g3"
down_revision = "0003_g2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_records",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("knowledge_group_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("question_original", sa.Text, nullable=False),
        sa.Column("question_normalised", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("tags", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("author_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approver_user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticket_id", pg.UUID(as_uuid=True), sa.ForeignKey("tickets.id")),
        sa.Column("supporting_references", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("validity", sa.String(20), nullable=False),
        sa.Column("status_reason", sa.Text),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding_model", sa.String(200), nullable=False),
        sa.Column("index_status", sa.String(20), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("validity IN ('ACTIVE', 'SUPERSEDED', 'REVOKED')", name="ck_knowledge_records_validity_enum"),
        sa.CheckConstraint("index_status IN ('PENDING', 'INDEXED', 'FAILED')", name="ck_knowledge_records_index_status_enum"),
        sa.UniqueConstraint("knowledge_group_id", "version", name="uq_knowledge_records_group_version"),
    )
    for c in ("knowledge_group_id", "author_user_id", "approver_user_id", "ticket_id"):
        op.create_index(f"ix_knowledge_records_{c}", "knowledge_records", [c])
    op.create_index("uq_knowledge_records_one_active", "knowledge_records", ["knowledge_group_id"], unique=True, postgresql_where=sa.text("validity = 'ACTIVE'"))
    op.create_foreign_key("fk_tickets_published_knowledge_id_knowledge_records", "tickets", "knowledge_records", ["published_knowledge_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_tickets_published_knowledge_id_knowledge_records", "tickets", type_="foreignkey")
    op.drop_table("knowledge_records")
