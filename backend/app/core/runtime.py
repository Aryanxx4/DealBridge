"""Process-wide runtime state determined at startup (reindex status, dependency checks)."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.core.config import BACKEND_ROOT
from app.core.enums import JobStatus

log = logging.getLogger("dealbridge.runtime")


class StartupError(RuntimeError):
    pass


@dataclass
class RuntimeState:
    reindex_required: bool = False
    reindex_problems: list[str] = field(default_factory=list)
    qdrant_checked: bool = False


STATE = RuntimeState()


def alembic_head() -> str | None:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return ScriptDirectory.from_config(cfg).get_current_head()


def check_migrations(db: Session) -> None:
    head = alembic_head()
    try:
        current = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:
        db.rollback()
        current = None
    if current != head:
        raise StartupError(f"Database revision is {current!r} but code expects {head!r}. Run make migrate.")


def fail_interrupted_jobs(db: Session) -> int:
    from app.models.system import Job

    res = db.execute(
        update(Job)
        .where(Job.status == JobStatus.RUNNING.value)
        .values(
            status=JobStatus.FAILED.value,
            error_code="INTERRUPTED",
            error_message="interrupted by restart",
            finished_at=datetime.now(UTC),
        )
    )
    db.commit()
    return res.rowcount or 0


def check_vectors(db: Session) -> None:
    from app.services.knowledge.state import reindex_problems
    from app.services.vector.qdrant_store import get_store

    store = get_store()
    try:
        problems = reindex_problems(db, store)
    except Exception as exc:  # Qdrant unreachable: serve, report degraded
        log.warning("qdrant check failed at startup", extra={"error": type(exc).__name__})
        STATE.qdrant_checked = False
        return
    STATE.qdrant_checked = True
    STATE.reindex_problems = problems
    STATE.reindex_required = bool(problems)
    if problems:
        log.warning("reindex required", extra={"problems": problems})


def load_embedder_in_background() -> None:
    from app.services.embeddings.embedder import get_embedder

    def _load():
        try:
            get_embedder().load()
        except Exception:
            pass  # recorded on the embedder; /api/health reports it

    threading.Thread(target=_load, name="embedder-load", daemon=True).start()
