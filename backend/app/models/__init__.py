"""Import every model module so Alembic autogenerate and metadata.create_all see all tables."""

from app.models.identity import Organization, User  # noqa: F401
from app.models.knowledge import IngestionRun, OkfFile  # noqa: F401
from app.models.system import AuditEvent, Job, KnowledgeState, VectorCollection  # noqa: F401
