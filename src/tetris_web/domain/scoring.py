from __future__ import annotations

from typing import Final

LINE_CLEAR_POINTS: Final[tuple[int, ...]] = (0, 100, 300, 500, 800)
GRAVITY_TICKS: Final[tuple[int, ...]] = (48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5)


def line_clear_points(cleared_lines: int, level: int) -> int:
    if not 0 <= cleared_lines <= 4:
        raise ValueError("cleared_lines must be between 0 and 4")
    if level < 1:
        raise ValueError("level must be positive")
    return LINE_CLEAR_POINTS[cleared_lines] * level


def level_for_lines(lines: int) -> int:
    if lines < 0:
        raise ValueError("lines must be non-negative")
    return lines // 10 + 1


def gravity_interval(level: int) -> int:
    if level < 1:
        raise ValueError("level must be positive")
    index = min(level - 1, len(GRAVITY_TICKS) - 1)
    return GRAVITY_TICKS[index]
