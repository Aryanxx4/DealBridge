"""In-process sliding-window rate limiter.

Not production-grade: state lives in one process and is lost on restart.
"""

from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque

from app.core.config import get_settings
from app.core.errors import AppError

# bucket name -> (max events, window seconds)
LIMITS: dict[str, tuple[int, int]] = {
    "chat": (30, 60),
    "upload": (10, 600),
    "job": (5, 600),  # extract and analyze
}

_lock = threading.Lock()
_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def check(bucket: str, user_id: str) -> None:
    if not get_settings().RATE_LIMIT_ENABLED:
        return
    limit, window = LIMITS[bucket]
    now = time.monotonic()
    key = (bucket, user_id)
    with _lock:
        q = _events[key]
        while q and now - q[0] >= window:
            q.popleft()
        if len(q) >= limit:
            retry = max(1, math.ceil(window - (now - q[0])))
            raise AppError(
                "RATE_LIMITED",
                "Too many requests. Please wait before trying again.",
                429,
                {"retry_after_seconds": retry},
                headers={"Retry-After": str(retry)},
            )
        q.append(now)


def reset() -> None:
    with _lock:
        _events.clear()
