import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_lock = threading.Lock()
_hits = defaultdict(deque)
_DAY = 86400
_MINUTE = 60


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _over(queue, now, per_minute, per_day):
    while queue and now - queue[0] > _DAY:
        queue.popleft()
    if len(queue) >= per_day:
        return True
    recent = 0
    for stamp in reversed(queue):
        if now - stamp > _MINUTE:
            break
        recent += 1
    return recent >= per_minute


def rate_limit(name: str, per_minute: int, per_day: int, total_per_minute: int, total_per_day: int):
    def dependency(request: Request):
        now = time.time()
        with _lock:
            per_ip = _hits[(name, _client_ip(request))]
            everyone = _hits[(name, "*")]
            if _over(per_ip, now, per_minute, per_day) or _over(everyone, now, total_per_minute, total_per_day):
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests right now. Please wait a minute and try again.",
                )
            per_ip.append(now)
            everyone.append(now)

    return dependency
