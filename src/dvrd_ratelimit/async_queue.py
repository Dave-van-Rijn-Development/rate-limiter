from asyncio import Queue
from collections import deque


class AsyncQueue(Queue):
    @property
    def queue(self) -> deque:
        return self._queue
