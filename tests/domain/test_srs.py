from tetris_web.domain.board import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    board_with_cells,
    empty_board,
    rotate_piece,
)
from tetris_web.domain.model import ActivePiece, PieceType, Rotation
from tetris_web.domain.tetrominoes import absolute_cells


def test_jlstz_rotation_kicks_away_from_left_wall() -> None:
    piece = ActivePiece(PieceType.T, Rotation.RIGHT, x=-1, y=5)

    rotated = rotate_piece(empty_board(), piece, direction=1)

    assert rotated.rotation is Rotation.REVERSE
    assert rotated.x == 0


def test_i_rotation_uses_its_distinct_right_wall_kick() -> None:
    piece = ActivePiece(PieceType.I, Rotation.RIGHT, x=7, y=5)

    rotated = rotate_piece(empty_board(), piece, direction=1)

    assert rotated.rotation is Rotation.REVERSE
    assert rotated.x == 6


def test_blocked_rotation_leaves_piece_unchanged() -> None:
    piece = ActivePiece(PieceType.T, Rotation.SPAWN, x=3, y=8)
    current_cells = set(absolute_cells(piece))
    blockers = {
        (x, y): PieceType.Z
        for y in range(BOARD_HEIGHT)
        for x in range(BOARD_WIDTH)
        if (x, y) not in current_cells
    }

    assert rotate_piece(board_with_cells(blockers), piece, direction=1) == piece


def test_counterclockwise_rotation_wraps_from_spawn_to_left() -> None:
    piece = ActivePiece(PieceType.L, Rotation.SPAWN, x=3, y=5)

    rotated = rotate_piece(empty_board(), piece, direction=-1)

    assert rotated.rotation is Rotation.LEFT
