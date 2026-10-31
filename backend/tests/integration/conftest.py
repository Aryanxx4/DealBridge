import shutil
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.core.config import BACKEND_ROOT, get_settings
from app.db import session as db_session
from app.services.embeddings.embedder import get_embedder
from app.services.seed import seed_identities
from app.services.vector.qdrant_store import QdrantStore, set_store

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def pytest_collection_modifyitems(items):
    for item in items:
        if "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def test_database():
    s = get_settings()
    assert s.DATABASE_URL.endswith("/dealbridge_test"), "integration tests must use dealbridge_test"
    admin_url = s.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(
            text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'dealbridge_test' AND pid <> pg_backend_pid()")
        )
        c.execute(text("DROP DATABASE IF EXISTS dealbridge_test"))
        c.execute(text("CREATE DATABASE dealbridge_test"))
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(cfg, "head")
    db_session.init_engine(s.DATABASE_URL)
    yield s.DATABASE_URL
    db_session.get_engine().dispose()
    with admin.connect() as c:
        c.execute(
            text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'dealbridge_test' AND pid <> pg_backend_pid()")
        )
        c.execute(text("DROP DATABASE IF EXISTS dealbridge_test"))
    admin.dispose()


@pytest.fixture(scope="session")
def embedder():
    e = get_embedder()
    e.load()
    return e


@pytest.fixture()
def store(test_database):
    s = get_settings()
    st = QdrantStore(s.QDRANT_URL, s.QDRANT_API_KEY, s.QDRANT_OFFICIAL_COLLECTION, s.QDRANT_RESOLVED_COLLECTION, s.EMBEDDING_DIMENSION)
    assert st.official.startswith("test_") and st.resolved.startswith("test_")
    st.init_collections(recreate_official=True, recreate_resolved=True)
    set_store(st)
    yield st
    set_store(None)


@pytest.fixture()
def db(test_database, store):
    """A clean database (all tables truncated, demo identities seeded) for each test."""
    engine = db_session.get_engine()
    with engine.begin() as c:
        tables = [
            r[0] for r in c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'"))
        ]
        c.execute(text("TRUNCATE " + ", ".join(f'"{t}"' for t in tables) + " RESTART IDENTITY CASCADE"))
        c.execute(text("INSERT INTO knowledge_state (id, epoch) VALUES (1, 0)"))
    from app.services.knowledge.state import record_collection

    session = db_session.session_factory()()
    seed_identities(session)
    record_collection(session, store.official)
    record_collection(session, store.resolved)
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def mini_bundle(tmp_path):
    """A writable copy of the synthetic AcmeLake OKF bundle (no IOMETE facts)."""
    dst = tmp_path / "okf_mini"
    shutil.copytree(FIXTURES / "okf_mini", dst)
    return dst
