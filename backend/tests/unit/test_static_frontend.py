"""Single-container deploys: the backend serves the built frontend when STATIC_DIR is set."""

from fastapi.testclient import TestClient

import app.main as main
from app.core.config import load_settings


def _app(monkeypatch, static_dir):
    s = load_settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://x:y@h/db",
        QDRANT_URL="http://q",
        APP_SECRET_KEY="k",
        STATIC_DIR=str(static_dir),
    )
    monkeypatch.setattr(main, "get_settings", lambda: s)
    return TestClient(main.create_app(skip_startup_checks=True))


def test_spa_routes_assets_and_api_404(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    c = _app(monkeypatch, tmp_path)
    assert c.get("/").text == "<html>app</html>"
    assert c.get("/buyer/assessments/123").text == "<html>app</html>"  # client-side route
    assert c.get("/assets/app.js").text == "console.log(1)"
    assert c.get("/favicon.svg").text == "<svg/>"
    r = c.get("/api/does-not-exist")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    assert c.get("/../../etc/passwd").text == "<html>app</html>"  # never escapes the dist folder
