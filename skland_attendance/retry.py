from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry(fn: Callable[[], T], *, retries: int, delay: float = 1.0, on_retry: Callable[[int, BaseException], None] | None = None) -> T:
    while True:
        try:
            return fn()
        except Exception as exc:
            if retries <= 0:
                raise
            if on_retry:
                on_retry(retries, exc)
            retries -= 1
            time.sleep(delay)
