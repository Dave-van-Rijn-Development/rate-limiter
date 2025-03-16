import time
from asyncio import Lock as AsyncLock, sleep
from collections.abc import MutableMapping
from functools import wraps
from threading import Lock
from typing import Callable, Awaitable, Any
from weakref import WeakValueDictionary

from dvrd_ratelimit.rate import Rate, AsyncRate


class RateLimitExceeded(Exception):
    def __init__(self, *args, wait_time: float, rate: Rate | AsyncRate):
        super().__init__(*args)
        self.wait_time = wait_time
        self.rate = rate


class Limiter:
    def __init__(self, rate: Rate):
        self._rate: Rate = rate
        self._rates: MutableMapping[str, Rate] = dict()
        self._locks = WeakValueDictionary()
        self._access_lock = Lock()

    def ratelimit(self, identity: str, delay: bool = True, max_delay: int = 0, return_bool: bool = False,
                  _with_lock: bool = True):
        with self._get_lock(identity=identity):
            max_delay_to = time.monotonic() + max_delay
            rate = self._rates.setdefault(identity, self._rate.clone())
            while True:
                if rate.try_acquire():
                    break
                wait_time = rate.get_wait_time()
                if not delay:
                    if return_bool:
                        return False
                    raise RateLimitExceeded(wait_time=wait_time, rate=rate)
                if wait_time > 0:
                    if max_delay and (time.monotonic() + wait_time) > max_delay_to:
                        if return_bool:
                            return False
                        raise RateLimitExceeded('Waiting for rate limit would exceed max delay', wait_time=wait_time,
                                                rate=rate)
                    time.sleep(wait_time)
            return True

    def _get_lock(self, *, identity: str) -> Lock:
        with self._access_lock:
            return self._locks.setdefault(identity, Lock())

    def __call__(self, identity: str, delay: bool = True, max_delay: int = 0):
        def wrap(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self.ratelimit(identity=identity, delay=delay, max_delay=max_delay)
                return func(*args, **kwargs)

            return wrapper

        return wrap


class AsyncLimiter:
    def __init__(self, rate: Rate | AsyncRate):
        self._rate: AsyncRate = AsyncRate.ensure_async(rate)
        self._rates: MutableMapping[str, AsyncRate] = dict()
        self._locks = WeakValueDictionary()
        self._access_lock = AsyncLock()

    async def ratelimit(self, identity: str, delay: bool = True, max_delay: int = 0, return_bool: bool = False,
                        _with_lock: bool = True):
        async with await self._get_lock(identity=identity):
            max_delay_to = time.monotonic() + max_delay
            rate = self._rates.setdefault(identity, self._rate.clone())
            while True:
                if await rate.try_acquire():
                    break
                wait_time = rate.get_wait_time()
                if not delay:
                    if return_bool:
                        return False
                    raise RateLimitExceeded(wait_time=wait_time, rate=rate)
                if wait_time > 0:
                    if max_delay and (time.monotonic() + wait_time) > max_delay_to:
                        if return_bool:
                            return False
                        raise RateLimitExceeded('Waiting for rate limit would exceed max delay', wait_time=wait_time,
                                                rate=rate)
                    await sleep(wait_time)
            return True

    async def _get_lock(self, *, identity: str) -> AsyncLock:
        async with self._access_lock:
            return self._locks.setdefault(identity, AsyncLock())

    def __call__(self, identity: str, delay: bool = True, max_delay: int = 0):
        def wrap(func: Callable[[Any, ...], Awaitable]):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                await self.ratelimit(identity=identity, delay=delay, max_delay=max_delay)
                return await func(*args, **kwargs)

            return wrapper

        return wrap
