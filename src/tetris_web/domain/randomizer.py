from __future__ import annotations

import random
from collections import deque
from typing import Final

from tetris_web.domain.model import PieceType

PIECE_KINDS: Final[tuple[PieceType, ...]] = tuple(PieceType)


class SevenBag:
    """Yield a deterministic sequence of shuffled seven-piece bags."""

    def __init__(self, seed: int | str | bytes | bytearray | None = None) -> None:
        self._random = random.Random(seed)
        self._queue: deque[PieceType] = deque()

    def next_piece(self) -> PieceType:
        self._fill(1)
        return self._queue.popleft()

    def peek(self, count: int) -> tuple[PieceType, ...]:
        if count < 0:
            raise ValueError("count must be non-negative")
        self._fill(count)
        return tuple(list(self._queue)[:count])

    def _fill(self, count: int) -> None:
        while len(self._queue) < count:
            bag = list(PIECE_KINDS)
            self._random.shuffle(bag)
            self._queue.extend(bag)
