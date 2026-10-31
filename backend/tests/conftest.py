"""Shared test configuration. Tests always run with APP_ENV=test against isolated resources.

Integration tests use the database `dealbridge_test` and Qdrant collections prefixed `test_`; they never touch
development data.
"""

import os

os.environ["APP_ENV"] = "test"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["LLM_USE_FAKE"] = "true"
os.environ["ENABLE_FAITHFULNESS_CHECK"] = "true"
_dev_url = os.environ.get("DATABASE_URL") or "postgresql+psycopg://dealbridge:dealbridge@localhost:5433/dealbridge"
os.environ["DEALBRIDGE_DEV_DATABASE_URL"] = _dev_url
os.environ["DATABASE_URL"] = _dev_url.rsplit("/", 1)[0] + "/dealbridge_test"
os.environ["QDRANT_OFFICIAL_COLLECTION"] = "test_official_product_knowledge"
os.environ["QDRANT_RESOLVED_COLLECTION"] = "test_resolved_query_knowledge"
os.environ.setdefault("UPLOAD_DIR", "./.cache/test_uploads")
