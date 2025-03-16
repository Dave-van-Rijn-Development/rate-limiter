import time
from queue import Queue, Full
from asyncio import QueueFull

from dvrd_ratelimit.async_queue import AsyncQueue
from dvrd_ratelimit.enums import Duration


class Rate:
    def __init__(self, limit: int, duration: int | Duration):
        self.limit: int = limit
        self.duration: int = duration
        self._entries: Queue[float] = Queue(maxsize=limit)

    def try_acquire(self) -> bool:
        # Try to add an entry to the rate, fails if the rate is already full
        self._check_entries()
        if self.limit <= 0:
            return False
        try:
            self._entries.put_nowait(time.monotonic())
        except Full:
            return False
        else:
            return True

    def get_wait_time(self) -> float | int:
        if self._entries.qsize() > 0:
            last_entry = list(self._entries.queue)[-1]
            return self.duration - (time.monotonic() - last_entry)
        return self.duration

    def _check_entries(self):
        now = time.monotonic()
        discard_before = now - self.duration
        remove_items = 0
        for entry in list(self._entries.queue):
            if entry < discard_before:
                remove_items += 1
            else:
                break
        for _ in range(remove_items):
            self._entries.get()

    def clone(self) -> "Rate":
        return Rate(self.limit, self.duration)


class AsyncRate:
    @staticmethod
    def ensure_async(rate: "Rate | AsyncRate"):
        if isinstance(rate, Rate):
            rate = AsyncRate(limit=rate.limit, duration=rate.duration)
        return rate

    def __init__(self, limit: int, duration: int | Duration):
        self.limit: int = limit
        self.duration: int = duration
        self._entries: AsyncQueue[float] = AsyncQueue(maxsize=limit)

    async def try_acquire(self) -> bool:
        # Try to add an entry to the rate, fails if the rate is already full
        await self._check_entries()
        if self.limit <= 0:
            return False
        try:
            self._entries.put_nowait(time.monotonic())
        except QueueFull:
            return False
        else:
            return True

    def get_wait_time(self) -> float | int:
        if self._entries.qsize() > 0:
            last_entry = list(self._entries.queue)[-1]
            return self.duration - (time.monotonic() - last_entry)
        return self.duration

    async def _check_entries(self):
        now = time.monotonic()
        discard_before = now - self.duration
        remove_items = 0
        for entry in list(self._entries.queue):
            if entry < discard_before:
                remove_items += 1
            else:
                break
        for _ in range(remove_items):
            await self._entries.get()

    def clone(self) -> "AsyncRate":
        return AsyncRate(self.limit, self.duration)
