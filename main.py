from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

import pygame  # noqa: F401 - pygbag scans entry-point imports for web wheels.


def load_runtime() -> Callable[[], Awaitable[None]]:
    source = Path(__file__).resolve().parent / "src"
    sys.path.insert(0, str(source))
    from tetris_web.app.runtime import run

    return run


if __name__ == "__main__":
    asyncio.run(load_runtime()())
