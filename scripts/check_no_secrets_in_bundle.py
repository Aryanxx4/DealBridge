"""Fail if secrets could reach the frontend bundle or Git.

1. Scans frontend/dist (build it first) for API-key prefixes, the literal variable names LLM_API_KEY, QDRANT_API_KEY and
   APP_SECRET_KEY, and the current values of those variables from the environment / .env.
2. Runs `git grep` over tracked files for Anthropic, OpenAI-compatible and OpenRouter API-key prefixes.
"""

import re
import subprocess
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "frontend" / "dist"
NAMES = ["LLM_API_KEY", "QDRANT_API_KEY", "APP_SECRET_KEY"]
KEY_PATTERNS = [re.compile(rb"sk-ant-[A-Za-z0-9_-]{8,}"), re.compile(rb"\bsk-[A-Za-z0-9]{24,}")]


def secret_values() -> list[str]:
    try:
        from app.core.config import get_settings

        s = get_settings()
        return [v for v in (s.LLM_API_KEY, s.QDRANT_API_KEY, s.APP_SECRET_KEY) if v and len(v) >= 8 and v != "change-me"]
    except Exception:
        return []


def scan_dist(values: list[str]) -> list[str]:
    problems = []
    if not DIST.exists():
        return [f"{DIST} does not exist: run `npm run build` in frontend/ first"]
    for f in DIST.rglob("*"):
        if not f.is_file():
            continue
        data = f.read_bytes()
        rel = f.relative_to(ROOT)
        for name in NAMES:
            if name.encode() in data:
                problems.append(f"{rel}: contains the variable name {name}")
        for pat in KEY_PATTERNS:
            if pat.search(data):
                problems.append(f"{rel}: contains an API-key-like string ({pat.pattern[:10]!r}...)")
        for v in values:
            if v.encode() in data:
                problems.append(f"{rel}: contains the current value of a secret")
    return problems


def scan_git(values: list[str]) -> list[str]:
    problems = []
    for pattern in ("sk-ant-", r"sk-[A-Za-z0-9]\{24,\}"):
        r = subprocess.run(
            ["git", "grep", "-nI", "-e", pattern, "--", ".", ":!scripts/check_no_secrets_in_bundle.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if r.stdout.strip():
            problems += [f"git: {line[:160]}" for line in r.stdout.strip().splitlines()]
    for v in values:
        r = subprocess.run(["git", "grep", "-nIF", "-e", v], cwd=ROOT, capture_output=True, text=True)
        if r.stdout.strip():
            problems.append("git: a tracked file contains the current value of a secret")
    tracked = subprocess.run(["git", "ls-files", ".env"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if tracked:
        problems.append("git: .env is tracked")
    return problems


def main() -> int:
    values = secret_values()
    problems = scan_dist(values) + scan_git(values)
    if problems:
        print("Secret check FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(
        f"Secret check passed: frontend/dist ({sum(1 for f in DIST.rglob('*') if f.is_file())} files) and tracked Git files contain no secrets."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
