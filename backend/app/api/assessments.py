"""Buyer assessment and requirement-intake endpoints. Ownership failures return 404 (never 403)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.config import get_settings
from app.core.enums import AuditAction, JobType
from app.core.errors import AppError, not_found
from app.core.identity import require_role
from app.db.session import get_db
from app.models.assessment import Assessment, ChangeProposal, Requirement, RequirementRevision, UploadedDocument
from app.models.chat import Message
from app.models.identity import User
from app.schemas.assessment import (
    ApplyProposalIn,
    AssessmentCreate,
    AssessmentOut,
    AssessmentPatch,
    DocumentOut,
    ExtractRequest,
    IntakeMessageIn,
    RequirementCreate,
    RequirementOut,
    RequirementPatch,
)
from app.schemas.common import JobAccepted
from app.services.assessment import extract_chat, extract_form, extract_pdf
from app.services.assessment import requirement_service as RS
from app.services.audit import audit
from app.services.ingestion.pdf_reader import store_buyer_pdf
from app.services.jobs import active_job, create_job, run_job

router = APIRouter(tags=["assessments"])
buyer = require_role("BUYER")


def owned_assessment(db: Session, user: User, assessment_id: uuid.UUID) -> Assessment:
    a = db.get(Assessment, assessment_id)
    if a is None or a.owner_user_id != user.id:
        raise not_found("Assessment")
    return a


def owned_requirement(db: Session, user: User, requirement_id: uuid.UUID) -> tuple[Assessment, Requirement]:
    r = db.get(Requirement, requirement_id)
    if r is None:
        raise not_found("Requirement")
    a = owned_assessment(db, user, r.assessment_id)
    return a, r


def _counts(db: Session, a: Assessment) -> tuple[int, int]:
    total = db.scalar(select(func.count(Requirement.id)).where(Requirement.assessment_id == a.id, Requirement.is_removed.is_(False))) or 0
    confirmed = (
        db.scalar(
            select(func.count(Requirement.id)).where(
                Requirement.assessment_id == a.id, Requirement.is_removed.is_(False), Requirement.buyer_confirmed.is_(True)
            )
        )
        or 0
    )
    return total, confirmed


def _out(db: Session, a: Assessment) -> AssessmentOut:
    return AssessmentOut.of(a, *_counts(db, a))


# ---- assessments -----------------------------------------------------------------------------
@router.post("/assessments", response_model=AssessmentOut, status_code=201)
def create_assessment(body: AssessmentCreate, user: User = Depends(buyer), db: Session = Depends(get_db)):
    ctx = {k: v.strip() for k, v in body.context.model_dump().items() if isinstance(v, str) and v.strip()}
    a = Assessment(owner_user_id=user.id, organization_id=user.organization_id, title=body.title.strip(), context=ctx)
    db.add(a)
    db.flush()
    audit(db, AuditAction.ASSESSMENT_CREATED, "assessment", a.id, user, {"title": a.title})
    db.commit()
    return _out(db, a)


@router.get("/assessments", response_model=list[AssessmentOut])
def list_assessments(limit: int = 50, offset: int = 0, user: User = Depends(buyer), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Assessment)
        .where(Assessment.owner_user_id == user.id)
        .order_by(Assessment.updated_at.desc())
        .limit(max(1, min(limit, 200)))
        .offset(offset)
    ).all()
    return [_out(db, a) for a in rows]


@router.get("/assessments/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    return _out(db, owned_assessment(db, user, assessment_id))


@router.patch("/assessments/{assessment_id}", response_model=AssessmentOut)
def patch_assessment(assessment_id: uuid.UUID, body: AssessmentPatch, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    if body.title is not None:
        a.title = body.title.strip()
    if body.context is not None:
        a.context = {**(a.context or {}), **{k: v.strip() for k, v in body.context.model_dump().items() if isinstance(v, str)}}
        a.context = {k: v for k, v in a.context.items() if v}
    db.commit()
    return _out(db, a)


# ---- documents -------------------------------------------------------------------------------
@router.post("/assessments/{assessment_id}/documents", response_model=DocumentOut, status_code=201)
def upload_document(
    assessment_id: uuid.UUID, request: Request, file: UploadFile = File(...), user: User = Depends(buyer), db: Session = Depends(get_db)
):
    a = owned_assessment(db, user, assessment_id)
    ratelimit.check("upload", str(user.id))
    limit = get_settings().MAX_UPLOAD_MB * 1024 * 1024
    clen = request.headers.get("content-length")
    if clen and clen.isdigit() and int(clen) > limit + 64 * 1024:
        raise AppError("FILE_TOO_LARGE", f"The file exceeds the {get_settings().MAX_UPLOAD_MB} MB limit.", 413)
    stored = store_buyer_pdf(file.file, file.content_type, a.id)
    doc = UploadedDocument(
        id=stored.document_id,
        assessment_id=a.id,
        uploaded_by=user.id,
        kind="BUYER_PDF",
        original_filename=(file.filename or "document.pdf")[:255],
        stored_path=str(stored.path),
        sha256=stored.sha256,
        size_bytes=stored.size_bytes,
        mime_type="application/pdf",
        page_count=stored.page_count,
        pages=stored.pages,
        extraction_status=stored.extraction_status,
        extraction_message=stored.extraction_message,
    )
    db.add(doc)
    audit(
        db,
        AuditAction.DOCUMENT_UPLOADED,
        "uploaded_document",
        doc.id,
        user,
        {"assessment_id": str(a.id), "pages": stored.page_count, "status": stored.extraction_status},
    )
    db.commit()
    return DocumentOut.of(doc)


@router.get("/assessments/{assessment_id}/documents", response_model=list[DocumentOut])
def list_documents(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    rows = db.scalars(
        select(UploadedDocument)
        .where(UploadedDocument.assessment_id == a.id, UploadedDocument.kind == "BUYER_PDF")
        .order_by(UploadedDocument.created_at.desc())
    ).all()
    return [DocumentOut.of(d) for d in rows]


@router.post("/assessments/{assessment_id}/requirements/extract", response_model=JobAccepted, status_code=202)
def extract(
    assessment_id: uuid.UUID, body: ExtractRequest, background: BackgroundTasks, user: User = Depends(buyer), db: Session = Depends(get_db)
):
    a = owned_assessment(db, user, assessment_id)
    doc = db.get(UploadedDocument, body.document_id)
    if doc is None or doc.assessment_id != a.id:
        raise not_found("Document")
    if doc.extraction_status != "OK":
        raise AppError("DOCUMENT_NOT_EXTRACTABLE", doc.extraction_message or "This document has no extractable text.", 422)
    if a.status == "ANALYZING" or active_job(db, JobType.EXTRACT_PDF.value, a.id) or active_job(db, JobType.ANALYZE.value, a.id):
        raise AppError("JOB_IN_PROGRESS", "Another job is already running for this assessment.", 409)
    from app.services.llm.client import get_llm

    get_llm()  # fail fast with LLM_NOT_CONFIGURED before queueing
    ratelimit.check("job", str(user.id))
    job = create_job(db, JobType.EXTRACT_PDF.value, user, a.id)
    db.commit()
    aid, did, uid = a.id, doc.id, user.id

    def fn(session: Session, ctx) -> dict:
        return extract_pdf.run_extraction(session, aid, did, session.get(User, uid), ctx.progress)

    background.add_task(run_job, job.id, fn)
    return JobAccepted(job_id=job.id)


@router.post("/assessments/{assessment_id}/form")
def submit_form(assessment_id: uuid.UUID, form: dict, user: User = Depends(buyer), db: Session = Depends(get_db)):
    owned_assessment(db, user, assessment_id)
    a = RS.lock_assessment(db, assessment_id)
    allowed = set(extract_form.FIELDS) | {"priorities"}
    clean = {k: v for k, v in form.items() if k in allowed and (isinstance(v, str) or (k == "priorities" and isinstance(v, dict)))}
    for k, v in clean.items():
        if isinstance(v, str) and len(v) > 4000:
            raise AppError("VALIDATION_ERROR", f"{k} is too long (4,000 characters max).", 422)
    return extract_form.submit(db, a, user, clean)


# ---- requirements ----------------------------------------------------------------------------
@router.get("/assessments/{assessment_id}/requirements", response_model=list[RequirementOut])
def list_requirements(assessment_id: uuid.UUID, include_removed: bool = False, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    q = select(Requirement).where(Requirement.assessment_id == a.id)
    if not include_removed:
        q = q.where(Requirement.is_removed.is_(False))
    return [RequirementOut.of(r) for r in db.scalars(q.order_by(Requirement.seq))]


@router.post("/assessments/{assessment_id}/requirements", response_model=RequirementOut, status_code=201)
def add_requirement(assessment_id: uuid.UUID, body: RequirementCreate, user: User = Depends(buyer), db: Session = Depends(get_db)):
    owned_assessment(db, user, assessment_id)
    a = RS.lock_assessment(db, assessment_id)
    r = RS.create(
        db,
        a,
        RS.Actor(user, "UI"),
        original_text=body.normalized_text,
        normalized_text=body.normalized_text,
        category=body.category,
        priority=body.priority,
        source_type="MANUAL",
        buyer_confirmed=True,
    )
    db.commit()
    return RequirementOut.of(r)


@router.patch("/requirements/{requirement_id}", response_model=RequirementOut)
def patch_requirement(requirement_id: uuid.UUID, body: RequirementPatch, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a, r = owned_requirement(db, user, requirement_id)
    a = RS.lock_assessment(db, a.id)
    fields = body.model_dump(exclude_unset=True)
    r = RS.edit(db, a, r.id, RS.Actor(user, "UI"), **fields)
    db.commit()
    return RequirementOut.of(r)


@router.delete("/requirements/{requirement_id}", response_model=RequirementOut)
def delete_requirement(requirement_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a, r = owned_requirement(db, user, requirement_id)
    a = RS.lock_assessment(db, a.id)
    r = RS.remove(db, a, r.id, RS.Actor(user, "UI"))
    db.commit()
    return RequirementOut.of(r)


def _simple(action):
    def endpoint(requirement_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
        a, r = owned_requirement(db, user, requirement_id)
        a = RS.lock_assessment(db, a.id)
        r = action(db, a, r.id, RS.Actor(user, "UI"))
        db.commit()
        return RequirementOut.of(r)

    return endpoint


router.add_api_route("/requirements/{requirement_id}/restore", _simple(RS.restore), methods=["POST"], response_model=RequirementOut)
router.add_api_route("/requirements/{requirement_id}/confirm", _simple(RS.confirm), methods=["POST"], response_model=RequirementOut)
router.add_api_route(
    "/requirements/{requirement_id}/waive-clarification", _simple(RS.waive_clarification), methods=["POST"], response_model=RequirementOut
)


@router.post("/assessments/{assessment_id}/requirements/confirm-all")
def confirm_all(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    owned_assessment(db, user, assessment_id)
    a = RS.lock_assessment(db, assessment_id)
    done = RS.confirm_all(db, a, RS.Actor(user, "UI"))
    db.commit()
    return {"confirmed": [r.display_id for r in done]}


@router.get("/requirements/{requirement_id}/history")
def history(requirement_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    _, r = owned_requirement(db, user, requirement_id)
    names = {u.id: u.display_name for u in db.scalars(select(User))}
    revs = db.scalars(
        select(RequirementRevision).where(RequirementRevision.requirement_id == r.id).order_by(RequirementRevision.revision_no)
    ).all()
    return [
        {
            "revision_no": v.revision_no,
            "change_type": v.change_type,
            "changes": v.changes,
            "actor": names.get(v.actor_user_id, v.actor_role),
            "origin": v.origin,
            "assessment_revision": v.assessment_revision,
            "created_at": v.created_at,
        }
        for v in revs
    ]


# ---- requirement intake chat -----------------------------------------------------------------
def _proposal_out(p: ChangeProposal | None) -> dict | None:
    if p is None:
        return None
    return {
        "id": str(p.id),
        "status": p.status,
        "ops": p.ops,
        "applied_op_indexes": p.applied_op_indexes,
        "result": p.result,
        "message_id": str(p.message_id) if p.message_id else None,
    }


@router.get("/assessments/{assessment_id}/intake-chat")
def get_intake(assessment_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    c = extract_chat.intake_conversation(db, a, user, create=False)
    if c is None:
        return {"messages": [], "proposals": []}
    msgs = db.scalars(select(Message).where(Message.conversation_id == c.id).order_by(Message.created_at)).all()
    props = db.scalars(select(ChangeProposal).where(ChangeProposal.assessment_id == a.id).order_by(ChangeProposal.created_at)).all()
    return {
        "messages": [
            {"id": str(m.id), "role": m.role, "content": m.content, "structured": m.structured, "created_at": m.created_at} for m in msgs
        ],
        "proposals": [_proposal_out(p) for p in props],
    }


@router.post("/assessments/{assessment_id}/intake-chat/messages")
def intake_message(assessment_id: uuid.UUID, body: IntakeMessageIn, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    ratelimit.check("chat", str(user.id))
    um, am, proposal = extract_chat.send(db, a, user, body.content.strip())
    return {
        "user_message": {"id": str(um.id), "role": "USER", "content": um.content, "created_at": um.created_at},
        "assistant_message": {
            "id": str(am.id),
            "role": "ASSISTANT",
            "content": am.content,
            "structured": am.structured,
            "created_at": am.created_at,
        },
        "proposal": _proposal_out(proposal),
    }


@router.post("/assessments/{assessment_id}/change-proposals/{proposal_id}/apply")
def apply_proposal(
    assessment_id: uuid.UUID, proposal_id: uuid.UUID, body: ApplyProposalIn, user: User = Depends(buyer), db: Session = Depends(get_db)
):
    owned_assessment(db, user, assessment_id)
    a = RS.lock_assessment(db, assessment_id)
    result = extract_chat.apply(db, a, proposal_id, user, body.selected_op_indexes)
    return result | {"assessment": _out(db, a).model_dump(mode="json")}


@router.post("/assessments/{assessment_id}/change-proposals/{proposal_id}/dismiss")
def dismiss_proposal(assessment_id: uuid.UUID, proposal_id: uuid.UUID, user: User = Depends(buyer), db: Session = Depends(get_db)):
    a = owned_assessment(db, user, assessment_id)
    return _proposal_out(extract_chat.dismiss(db, a, proposal_id))
