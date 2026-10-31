"""Shared test configuration. Tests always run with APP_ENV=test."""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
