"""Brute-force protection for sign-in.

Failed attempts are counted in a sliding window, keyed two ways:
- per (client IP, email): stops password guessing against one account, without letting a
  stranger lock someone else out from a different IP;
- per client IP: stops one machine from trying many accounts (credential stuffing).

State lives in memory, which fits this single-process app. Running several API processes or
servers would need a shared store such as Redis so they see the same counts.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from knowledge_worker.core.exceptions import TooManyRequestsError

# Drop empty keys once the table gets this big, so random emails can't grow memory forever.
_SWEEP_AT = 10_000


class LoginRateLimiter:
    def __init__(
        self,
        max_failures: int,
        max_failures_per_ip: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_failures = max_failures
        self.max_failures_per_ip = max_failures_per_ip
        self.window_seconds = window_seconds
        self.clock = clock
        self._failures: dict[tuple[str, ...], deque[float]] = {}
        self._lock = threading.Lock()  # sync endpoints run in a threadpool

    @staticmethod
    def _keys(ip: str, email: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return ("account", ip, email.strip().lower()), ("ip", ip)

    def _recent(self, key: tuple[str, ...], now: float) -> deque[float]:
        times = self._failures.get(key)
        if times is None:
            return deque()
        while times and times[0] <= now - self.window_seconds:
            times.popleft()
        if not times:
            del self._failures[key]
        return times

    def check(self, ip: str, email: str) -> None:
        """Raise TooManyRequestsError if this IP or this IP+email is currently blocked."""
        now = self.clock()
        account_key, ip_key = self._keys(ip, email)
        with self._lock:
            waits = [
                times[0] + self.window_seconds - now
                for key, limit in ((account_key, self.max_failures), (ip_key, self.max_failures_per_ip))
                if len(times := self._recent(key, now)) >= limit
            ]
        if waits:
            retry_after = max(1, math.ceil(max(waits)))
            minutes = math.ceil(retry_after / 60)
            raise TooManyRequestsError(
                f"Too many failed sign-in attempts. Try again in {minutes} minute"
                f"{'' if minutes == 1 else 's'}.",
                retry_after_seconds=retry_after,
            )

    def record_failure(self, ip: str, email: str) -> None:
        now = self.clock()
        with self._lock:
            if len(self._failures) >= _SWEEP_AT:
                for key in list(self._failures):
                    self._recent(key, now)
            for key in self._keys(ip, email):
                self._failures.setdefault(key, deque()).append(now)

    def reset(self, ip: str, email: str) -> None:
        """Clear the account counter after a successful sign-in. The per-IP count stays, so a
        valid login can't be used to reset the budget for guessing other accounts."""
        account_key, _ = self._keys(ip, email)
        with self._lock:
            self._failures.pop(account_key, None)
