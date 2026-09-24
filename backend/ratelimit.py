"""Minimal in-process rate limiting — per the Prototype Plan's security table:
"Rate Limiting: Yes (basic) ... FastAPI slowapi or hosting platform limits".
Hand-rolled instead of adding the slowapi dependency, since a sliding-window
counter per (client IP, bucket) is ~30 lines and this only needs to survive a
single-process demo, not a multi-worker production deployment.

/api/login gets a stricter limit than everything else, since it's the one
endpoint an attacker could use to brute-force the (intentionally weak) demo
passwords.
"""
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# (max_requests, window_seconds) per path prefix; first match wins.
LIMITS = [
    ("/api/login", (5, 10)),
    ("/api/", (30, 10)),
]

_hits: dict[tuple[str, str], list[float]] = defaultdict(list)


def _bucket_for(path: str) -> tuple[str, int, int] | None:
    for prefix, (max_requests, window) in LIMITS:
        if path.startswith(prefix):
            return prefix, max_requests, window
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        bucket = _bucket_for(request.url.path)
        if bucket is None:
            return await call_next(request)

        prefix, max_requests, window = bucket
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, prefix)
        now = time.time()

        timestamps = _hits[key]
        cutoff = now - window
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for {prefix} — max {max_requests} requests per {window}s."},
            )
        timestamps.append(now)
        return await call_next(request)
