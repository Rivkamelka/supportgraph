"""A lightweight, in-memory, fixed-window rate limiter for /api/ask.

Deliberately simple, and deliberately honest about its limits: on a
serverless platform such as Vercel, each function instance owns its own
process memory, and a cold start wipes it, so this does NOT hold a limit
across every instance or across a redeploy the way a shared store (Redis,
Upstash) would. It is still worth having as a zero-infrastructure first
layer against a single client hammering the endpoint within one warm
instance -- the same tradeoff the sibling "Insight" project's own
in-memory limiter makes. See docs/adr/0005-production-hardening.md for
why this is judged good enough for a demo deployment and what a real
production rollout would swap it for.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

DEFAULT_MAX_REQUESTS = 20
DEFAULT_WINDOW_SECONDS = 60

# module-level so it persists across requests within the same warm
# instance/process, without needing a class the caller has to instantiate
_hits: dict[str, deque[float]] = defaultdict(deque)


def is_rate_limited(
    client_key: str,
    *,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> tuple[bool, int]:
    """Returns (limited, retry_after_seconds). Safe to call from a sync
    request handler; not thread-safe under true parallel access, which is
    an acceptable tradeoff for a single-worker demo deployment."""
    now = time.monotonic()
    hits = _hits[client_key]

    while hits and now - hits[0] > window_seconds:
        hits.popleft()

    if len(hits) >= max_requests:
        retry_after = max(1, int(window_seconds - (now - hits[0])) + 1)
        return True, retry_after

    hits.append(now)
    return False, 0


def reset_all() -> None:
    """Test-only helper: clears all tracked clients between test cases."""
    _hits.clear()
