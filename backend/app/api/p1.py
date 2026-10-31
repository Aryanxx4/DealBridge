"""P1 features: Excel export, follow-up owner assignment, seller documents."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.assessments import owned_assessment
from app.core import ratelimit
from app.core.config import get_settings
from app.core.enums import AuditAction
from app.core.errors import AppError, forbidden_role, invalid_state, not_found
from app.core.identity import get_current_user, require_role
from app.db.session import get_db
from app.models.assessment import Assessment, UploadedDocument
from app.models.identity import User
from app.models.sharing import FollowUpMessage, SellerResponse
from app.services.assessment.summary import build_results
from app.services.assessment.versions import get_version
from app.services.audit import audit
from app.services.ingestion.pdf_reader import save_stream
from app.services.reports.pdf_report import slug
from app.services.reports.xlsx_export import build_xlsx
from app.services.sharing import followup_service as FU
from app.services.sharing import share_service as SH

router = APIRouter(tags=["p1"])
seller = require_role("SELLER")
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SELLER_DOC_TYPES = {".pdf": ("application/pdf", b"%PDF-"), ".md": ("text/markdown", None), ".txt": ("text/plain", None)}


@router.get("/assessments/{assessment_id}/report.xlsx")
def export_xlsx(
    assessment_id: uuid.UUID, version: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role == "BUYER":
        a = owned_assessment(db, user, assessment_id)
        v = get_version(db, a.id, version)
        results = build_results(db, a, v)
    elif user.role == "SELLER":
        a = SH.seller_assessment(db, user, assessment_id)
        v = SH.seller_version(db, user, a, version)
        results = build_results(db, a, v, viewer="SELLER", include_tickets=False)
    else:
        raise forbidden_role()
    audit(db, AuditAction.REPORT_DOWNLOADED, "assessment", a.id, user, {"version_no": v.version_no, "format": "xlsx"})
    db.commit()
    name = f"DealBridge_Assessment_{slug(a.title)}_v{v.version_no}.xlsx"
    return Response(build_xlsx(results), media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{name}"'})


class OwnerIn(BaseModel):
    owner_user_id: uuid.UUID | None = None


@router.patch("/follow-ups/{follow_up_id}/owner")
def assign_owner(follow_up_id: uuid.UUID, body: OwnerIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    if f.status == "CLOSED":
        raise invalid_state("A closed follow-up cannot be reassigned.")
    if body.owner_user_id is not None:
        owner = db.get(User, body.owner_user_id)
        if owner is None or owner.organization_id != user.organization_id or owner.role != "SELLER":
            raise AppError("VALIDATION_ERROR", "The owner must be a seller in your organisation.", 422)
    f.assigned_owner_user_id = body.owner_user_id
    audit(db, AuditAction.FOLLOWUP_UPDATED, "follow_up", f.id, user, {"action": "assign_owner"})
    db.commit()
    return FU.out(db, f, user, True)


@router.get("/seller/team")
def seller_team(user: User = Depends(seller), db: Session = Depends(get_db)):
    return [
        {"id": str(u.id), "display_name": u.display_name}
        for u in db.scalars(
            select(User).where(User.organization_id == user.organization_id, User.role == "SELLER").order_by(User.display_name)
        )
    ]


# ---- seller documents (never embedded, indexed or merged into the OKF bundle) -----------------
@router.post("/seller/documents", status_code=201)
def upload_seller_document(request: Request, file: UploadFile = File(...), user: User = Depends(seller), db: Session = Depends(get_db)):
    ratelimit.check("upload", str(user.id))
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SELLER_DOC_TYPES:
        raise AppError("NOT_A_PDF", "Only PDF, Markdown (.md) and text (.txt) files are accepted.", 415)
    mime, magic = SELLER_DOC_TYPES[ext]
    doc_id = uuid.uuid4()
    path = get_settings().upload_dir / "seller" / str(user.organization_id) / f"{doc_id}{ext}"
    sha, size = save_stream(file.file, path, file.content_type if magic else None, require_pdf=magic is not None)
    if magic is None:
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            path.unlink(missing_ok=True)
            raise AppError("NOT_A_PDF", "Text files must be UTF-8.", 415) from None
    doc = UploadedDocument(
        id=doc_id,
        assessment_id=None,
        uploaded_by=user.id,
        kind="SELLER_DOC",
        original_filename=(file.filename or f"document{ext}")[:255],
        stored_path=str(path),
        sha256=sha,
        size_bytes=size,
        mime_type=mime,
        page_count=0,
        pages=[],
        extraction_status="OK",
        extraction_message="Seller-provided document (not official knowledge)",
    )
    db.add(doc)
    audit(db, AuditAction.DOCUMENT_UPLOADED, "uploaded_document", doc.id, user, {"kind": "SELLER_DOC"})
    db.commit()
    return {
        "id": str(doc.id),
        "original_filename": doc.original_filename,
        "size_bytes": size,
        "label": "Seller-provided document (not official knowledge)",
    }


def _can_download(db: Session, user: User, doc: UploadedDocument) -> bool:
    if doc.kind != "SELLER_DOC":
        return False
    uploader = db.get(User, doc.uploaded_by)
    if user.role == "SELLER":
        return uploader is not None and uploader.organization_id == user.organization_id
    if user.role != "BUYER":
        return False
    did = str(doc.id)
    attached_assessments = {r.assessment_id for r in db.scalars(select(SellerResponse)) if did in (r.attachment_document_ids or [])}
    for m in db.scalars(select(FollowUpMessage)):
        if did in (m.attachment_document_ids or []):
            from app.models.sharing import FollowUpRequest

            f = db.get(FollowUpRequest, m.follow_up_id)
            attached_assessments.add(f.assessment_id)
    return any((a := db.get(Assessment, aid)) is not None and a.owner_user_id == user.id for aid in attached_assessments)


@router.get("/documents/{document_id}/download")
def download_document(document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.get(UploadedDocument, document_id)
    if doc is None or not _can_download(db, user, doc):
        raise not_found("Document")
    return FileResponse(
        doc.stored_path, media_type=doc.mime_type, filename=doc.original_filename, headers={"X-Content-Type-Options": "nosniff"}
    )


class AttachIn(BaseModel):
    document_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)


def _own_docs(db: Session, user: User, ids: list[uuid.UUID]) -> list[str]:
    out = []
    for i in ids:
        d = db.get(UploadedDocument, i)
        if d is None or d.kind != "SELLER_DOC" or db.get(User, d.uploaded_by).organization_id != user.organization_id:
            raise not_found("Document")
        out.append(str(d.id))
    return out


@router.post("/seller-responses/{response_id}/attachments")
def attach_to_response(response_id: uuid.UUID, body: AttachIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    r = db.get(SellerResponse, response_id)
    if r is None or db.get(User, r.seller_user_id).organization_id != user.organization_id:
        raise not_found("Seller response")
    SH.seller_assessment(db, user, r.assessment_id)  # share must still be active
    r.attachment_document_ids = list(dict.fromkeys([*(r.attachment_document_ids or []), *_own_docs(db, user, body.document_ids)]))
    db.commit()
    return {"id": str(r.id), "attachment_document_ids": r.attachment_document_ids}


@router.post("/follow-ups/{follow_up_id}/attachments")
def attach_to_follow_up(follow_up_id: uuid.UUID, body: AttachIn, user: User = Depends(seller), db: Session = Depends(get_db)):
    f, _ = FU.access(db, user, follow_up_id)
    if f.status == "CLOSED":
        raise invalid_state("This follow-up is closed and read-only.")
    m = FollowUpMessage(
        follow_up_id=f.id,
        author_user_id=user.id,
        author_role=user.role,
        body="Attached seller-provided document(s).",
        attachment_document_ids=_own_docs(db, user, body.document_ids),
    )
    db.add(m)
    db.commit()
    return FU.out(db, f, user, True)
