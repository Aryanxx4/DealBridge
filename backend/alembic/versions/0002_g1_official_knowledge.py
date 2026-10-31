"""G1 official knowledge: okf_files, ingestion_runs

Revision ID: 0002_g1
Revises: 0001_g0
Create Date: 2026-10-31
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0002_g1"
down_revision = "0001_g0"
branch_labels = None
depends_on = None


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "okf_files",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("path", sa.String(500), nullable=False, unique=True),
        sa.Column("knowledge_id", sa.String(200)),
        sa.Column("title", sa.String(300)),
        sa.Column("category", sa.String(50)),
        sa.Column("source_url", sa.Text),
        sa.Column("last_verified_at", sa.String(40)),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("version", sa.Integer),
        sa.Column("approval_status", sa.String(20)),
        sa.Column("chunk_ids", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("chunk_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("last_ingested_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text),
        *_ts(),
        sa.CheckConstraint("status IN ('INDEXED', 'SKIPPED_NOT_APPROVED', 'REMOVED', 'ERROR')", name="ck_okf_files_status_enum"),
    )
    op.create_index("ix_okf_files_knowledge_id", "okf_files", ["knowledge_id"])
    op.create_table(
        "ingestion_runs",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("triggered_by", sa.String(100), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False),
        sa.Column("spec_conformance", sa.String(10), nullable=False),
        sa.Column("embedding_model", sa.String(200), nullable=False),
        sa.Column("files_scanned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("added", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unchanged", sa.Integer, nullable=False, server_default="0"),
        sa.Column("removed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunks_upserted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunks_deleted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("errors", pg.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(40), nullable=False),
        *_ts(),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_table("okf_files")
