import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_no_secrets_in_frontend_bundle():
    dist = ROOT / "frontend" / "dist"
    if not dist.exists():
        import pytest

        pytest.skip("frontend/dist not built (make test builds it after the backend tests; run make check-secrets)")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_no_secrets_in_bundle.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
