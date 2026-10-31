"""Import every model module so Alembic autogenerate and metadata.create_all see all tables."""

from app.models.assessment import (  # noqa: F401
    Assessment,
    AssessmentVersion,
    ChangeProposal,
    EvidenceReference,
    Requirement,
    RequirementAssessment,
    RequirementRevision,
    UploadedDocument,
)
from app.models.chat import Conversation, Message, Ticket, TicketOccurrence  # noqa: F401
from app.models.identity import Organization, User  # noqa: F401
from app.models.knowledge import IngestionRun, KnowledgeRecord, OkfFile  # noqa: F401
from app.models.system import AuditEvent, Job, KnowledgeState, VectorCollection  # noqa: F401
