from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class PieceType(StrEnum):
    I = "I"
    J = "J"
    L = "L"
    O = "O"
    S = "S"
    T = "T"
    Z = "Z"


class Rotation(IntEnum):
    SPAWN = 0
    RIGHT = 1
    REVERSE = 2
    LEFT = 3


class GameStatus(StrEnum):
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class Command(StrEnum):
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    SOFT_DROP = "soft_drop"
    HARD_DROP = "hard_drop"
    ROTATE_CLOCKWISE = "rotate_clockwise"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    HOLD = "hold"
    TOGGLE_PAUSE = "toggle_pause"
    RESTART = "restart"


type Cell = PieceType | None
type Board = tuple[tuple[Cell, ...], ...]
type Seed = int | str | bytes | bytearray | None


@dataclass(frozen=True, slots=True)
class ActivePiece:
    kind: PieceType
    rotation: Rotation
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class GameState:
    board: Board
    active: ActivePiece | None
    hold: PieceType | None
    next_queue: tuple[PieceType, ...]
    status: GameStatus
    score: int
    lines: int
    level: int
    tick: int
    gravity_ticks: int
    lock_ticks: int
    lock_resets: int
    can_hold: bool
    pieces_placed: int
    last_cleared: tuple[int, ...]
