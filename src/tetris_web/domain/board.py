from __future__ import annotations

from dataclasses import replace
from typing import Final

from tetris_web.domain.model import ActivePiece, Board, Cell, PieceType
from tetris_web.domain.tetrominoes import (
    absolute_cells,
    kick_offsets,
    next_rotation,
)

BOARD_WIDTH: Final = 10
VISIBLE_HEIGHT: Final = 20
HIDDEN_ROWS: Final = 4
BOARD_HEIGHT: Final = VISIBLE_HEIGHT + HIDDEN_ROWS


def empty_board() -> Board:
    return tuple(tuple(None for _ in range(BOARD_WIDTH)) for _ in range(BOARD_HEIGHT))


def is_valid_position(board: Board, piece: ActivePiece) -> bool:
    for x, y in absolute_cells(piece):
        if x < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
            return False
        if y >= 0 and board[y][x] is not None:
            return False
    return True


def move_piece(board: Board, piece: ActivePiece, dx: int, dy: int) -> ActivePiece | None:
    candidate = replace(piece, x=piece.x + dx, y=piece.y + dy)
    return candidate if is_valid_position(board, candidate) else None


def rotate_piece(board: Board, piece: ActivePiece, direction: int) -> ActivePiece:
    target_rotation = next_rotation(piece.rotation, direction)
    for dx, dy in kick_offsets(piece.kind, piece.rotation, target_rotation):
        candidate = replace(
            piece,
            rotation=target_rotation,
            x=piece.x + dx,
            y=piece.y + dy,
        )
        if is_valid_position(board, candidate):
            return candidate
    return piece


def drop_distance(board: Board, piece: ActivePiece) -> int:
    distance = 0
    while move_piece(board, piece, 0, distance + 1) is not None:
        distance += 1
    return distance


def lock_piece(board: Board, piece: ActivePiece) -> tuple[Board, bool]:
    rows = [list(row) for row in board]
    top_out = False
    for x, y in absolute_cells(piece):
        if y < 0:
            top_out = True
        else:
            rows[y][x] = piece.kind
    return tuple(tuple(row) for row in rows), top_out


def clear_full_lines(board: Board) -> tuple[Board, tuple[int, ...]]:
    cleared = tuple(
        index for index, row in enumerate(board) if all(cell is not None for cell in row)
    )
    if not cleared:
        return board, ()

    surviving_rows = [row for index, row in enumerate(board) if index not in cleared]
    blank_rows = [tuple(None for _ in range(BOARD_WIDTH)) for _ in cleared]
    return tuple(blank_rows + surviving_rows), cleared


def has_hidden_blocks(board: Board) -> bool:
    return any(cell is not None for row in board[:HIDDEN_ROWS] for cell in row)


def board_with_cells(cells: dict[tuple[int, int], Cell]) -> Board:
    rows = [list(row) for row in empty_board()]
    for (x, y), value in cells.items():
        if not (0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT):
            raise ValueError(f"cell {(x, y)} lies outside the board")
        rows[y][x] = value
    return tuple(tuple(row) for row in rows)


def count_filled_cells(board: Board, kind: PieceType | None = None) -> int:
    return sum(
        cell is not None and (kind is None or cell is kind)
        for row in board
        for cell in row
    )
