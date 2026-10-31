import uuid
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.core.identity import get_current_user, require_role


class FakeDb:
    def __init__(self, users):
        self.users = users

    def get(self, _model, uid):
        return self.users.get(uid)


def _user(role="BUYER"):
    return SimpleNamespace(id=uuid.uuid4(), role=role)


def test_missing_header_is_unknown_identity():
    with pytest.raises(AppError) as exc:
        get_current_user(None, FakeDb({}))
    assert exc.value.code == "UNKNOWN_IDENTITY" and exc.value.status_code == 401


def test_malformed_and_unknown_ids_rejected():
    for value in ("not-a-uuid", str(uuid.uuid4())):
        with pytest.raises(AppError) as exc:
            get_current_user(value, FakeDb({}))
        assert exc.value.code == "UNKNOWN_IDENTITY"


def test_known_user_resolves():
    u = _user()
    assert get_current_user(str(u.id), FakeDb({u.id: u})) is u


def test_require_role_allows_and_forbids():
    dep = require_role("ADMIN")
    admin, buyer = _user("ADMIN"), _user("BUYER")
    assert dep(admin) is admin
    with pytest.raises(AppError) as exc:
        dep(buyer)
    assert exc.value.code == "FORBIDDEN_ROLE" and exc.value.status_code == 403
