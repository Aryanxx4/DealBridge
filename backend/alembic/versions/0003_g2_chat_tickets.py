"""G2 chat and tickets: conversations, messages, tickets, ticket_occurrences

Revision ID: 0003_g2
Revises: 0002_g1
Create Date: 2026-10-31
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0003_g2"
down_revision = "0002_g1"
branch_labels = None
depends_on = None

ANSWER_TYPES = ["OFFICIAL_VERIFIED", "EXPERT_VERIFIED", "MIXED_VERIFIED", "GENERAL_EXPLANATION", "PARTIAL", "UNVERIFIED", "REDIRECT", "OUT_OF_SCOPE", "SMALL_TALK"]
TICKET_STATUSES = ["OPEN", "IN_REVIEW", "ANSWER_PROPOSED", "APPROVED", "REJECTED", "PUBLISHED", "CLOSED"]


def _in(col, vals):
    return f"{col} IN (" + ", ".join(f"'{v}'" for v in vals) + ")"


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def _uuid(name, fk=None, nullable=True):
    args = [sa.ForeignKey(fk)] if fk else []
    return sa.Column(name, pg.UUID(as_uuid=True), *args, nullable=nullable)


def upgrade() -> None:
    op.execute("CREATE SEQUENCE ticket_display_seq START 1")
    op.create_table(
        "conversations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("owner_user_id", "users.id", nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        _uuid("assessment_id"),
        _uuid("requirement_id"),
        sa.Column("title", sa.String(200), nullable=False),
        *_ts(),
        sa.CheckConstraint(_in("kind", ["PRODUCT_CHAT", "REQUIREMENT_INTAKE"]), name="ck_conversations_kind_enum"),
    )
    for c in ("owner_user_id", "assessment_id", "requirement_id"):
        op.create_index(f"ix_conversations_{c}", "conversations", [c])

    op.create_table(
        "tickets",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_id", sa.String(20), nullable=False, unique=True),
        sa.Column("original_question", sa.Text, nullable=False),
        sa.Column("normalised_question", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("occurrence_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("reason", sa.String(30), nullable=False),
        _uuid("created_by", "users.id", nullable=False),
        _uuid("conversation_id", "conversations.id"),
        _uuid("message_id"),
        _uuid("assessment_id"),
        _uuid("requirement_id"),
        sa.Column("context_excerpt", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("question_embedding", pg.ARRAY(sa.REAL)),
        sa.Column("retrieval_trace", pg.JSONB),
        sa.Column("related_knowledge_ids", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("proposed_answer", sa.Text),
        _uuid("proposed_by", "users.id"),
        sa.Column("proposed_at", sa.DateTime(timezone=True)),
        sa.Column("supporting_sources", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("internal_notes", sa.Text),
        _uuid("assigned_to", "users.id"),
        _uuid("reviewed_by", "users.id"),
        sa.Column("reviewer_note", sa.Text),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        _uuid("published_knowledge_id"),
        sa.Column("publish_error", sa.Text),
        sa.Column("close_reason", sa.String(40)),
        _uuid("duplicate_of"),
        *_ts(),
        sa.CheckConstraint(_in("status", TICKET_STATUSES), name="ck_tickets_status_enum"),
        sa.CheckConstraint(_in("priority", ["LOW", "MEDIUM", "HIGH"]), name="ck_tickets_priority_enum"),
        sa.CheckConstraint(_in("reason", ["NO_EVIDENCE", "WEAK_EVIDENCE", "CONFLICT", "PARTIAL", "USER_REQUESTED"]), name="ck_tickets_reason_enum"),
    )
    for c in ("status", "created_by", "conversation_id", "message_id", "assessment_id", "requirement_id", "proposed_by", "assigned_to", "reviewed_by", "published_knowledge_id"):
        op.create_index(f"ix_tickets_{c}", "tickets", [c])

    op.create_table(
        "messages",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("conversation_id", "conversations.id", nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("answer_type", sa.String(30)),
        sa.Column("citations", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        _uuid("ticket_id", "tickets.id"),
        sa.Column("retrieval_trace", pg.JSONB),
        sa.Column("structured", pg.JSONB),
        sa.Column("model", sa.String(100)),
        sa.Column("prompt_versions", pg.JSONB),
        *_ts(),
        sa.CheckConstraint(_in("role", ["USER", "ASSISTANT"]), name="ck_messages_role_enum"),
        sa.CheckConstraint(_in("answer_type", ANSWER_TYPES), name="ck_messages_answer_type_enum"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_ticket_id", "messages", ["ticket_id"])

    op.create_table(
        "ticket_occurrences",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        _uuid("ticket_id", "tickets.id", nullable=False),
        _uuid("user_id", "users.id", nullable=False),
        _uuid("conversation_id", "conversations.id"),
        _uuid("message_id"),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for c in ("ticket_id", "user_id", "conversation_id"):
        op.create_index(f"ix_ticket_occurrences_{c}", "ticket_occurrences", [c])


def downgrade() -> None:
    for t in ("ticket_occurrences", "messages", "tickets", "conversations"):
        op.drop_table(t)
    op.execute("DROP SEQUENCE ticket_display_seq")
