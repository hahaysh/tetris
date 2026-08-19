from __future__ import annotations

from typing import Final

from tetris_web.domain.model import ActivePiece, PieceType, Rotation

type Point = tuple[int, int]
type Orientation = tuple[Point, Point, Point, Point]
type KickKey = tuple[Rotation, Rotation]

ORIENTATIONS: Final[dict[PieceType, tuple[Orientation, ...]]] = {
    PieceType.I: (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    PieceType.J: (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    PieceType.L: (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    PieceType.O: (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    PieceType.S: (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    PieceType.T: (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    PieceType.Z: (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
}

# Official SRS offsets expressed in board coordinates, where positive y points down.
JLSTZ_KICKS: Final[dict[KickKey, tuple[Point, ...]]] = {
    (Rotation.SPAWN, Rotation.RIGHT): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (Rotation.RIGHT, Rotation.SPAWN): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (Rotation.RIGHT, Rotation.REVERSE): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (Rotation.REVERSE, Rotation.RIGHT): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (Rotation.REVERSE, Rotation.LEFT): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (Rotation.LEFT, Rotation.REVERSE): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (Rotation.LEFT, Rotation.SPAWN): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (Rotation.SPAWN, Rotation.LEFT): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

I_KICKS: Final[dict[KickKey, tuple[Point, ...]]] = {
    (Rotation.SPAWN, Rotation.RIGHT): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (Rotation.RIGHT, Rotation.SPAWN): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (Rotation.RIGHT, Rotation.REVERSE): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (Rotation.REVERSE, Rotation.RIGHT): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (Rotation.REVERSE, Rotation.LEFT): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (Rotation.LEFT, Rotation.REVERSE): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (Rotation.LEFT, Rotation.SPAWN): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (Rotation.SPAWN, Rotation.LEFT): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}


def local_cells(kind: PieceType, rotation: Rotation) -> Orientation:
    return ORIENTATIONS[kind][rotation]


def absolute_cells(piece: ActivePiece) -> Orientation:
    return tuple(
        (piece.x + local_x, piece.y + local_y)
        for local_x, local_y in local_cells(piece.kind, piece.rotation)
    )  # type: ignore[return-value]


def spawn_piece(kind: PieceType) -> ActivePiece:
    return ActivePiece(kind=kind, rotation=Rotation.SPAWN, x=3, y=2)


def next_rotation(rotation: Rotation, direction: int) -> Rotation:
    return Rotation((rotation + direction) % 4)


def kick_offsets(kind: PieceType, start: Rotation, end: Rotation) -> tuple[Point, ...]:
    if kind is PieceType.O:
        return ((0, 0),)
    table = I_KICKS if kind is PieceType.I else JLSTZ_KICKS
    return table[(start, end)]
