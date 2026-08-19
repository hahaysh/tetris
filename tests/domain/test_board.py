from dataclasses import replace

from tetris_web.domain.board import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    HIDDEN_ROWS,
    board_with_cells,
    clear_full_lines,
    count_filled_cells,
    drop_distance,
    empty_board,
    has_hidden_blocks,
    is_valid_position,
    lock_piece,
)
from tetris_web.domain.model import PieceType
from tetris_web.domain.tetrominoes import spawn_piece


def test_empty_board_has_hidden_and_visible_rows() -> None:
    board = empty_board()

    assert len(board) == BOARD_HEIGHT
    assert all(len(row) == BOARD_WIDTH for row in board)
    assert count_filled_cells(board) == 0


def test_collision_rejects_walls_floor_and_filled_cells() -> None:
    board = board_with_cells({(4, 10): PieceType.Z})
    piece = spawn_piece(PieceType.O)

    assert not is_valid_position(board, replace(piece, x=-2))
    assert not is_valid_position(board, replace(piece, y=BOARD_HEIGHT - 1))
    assert not is_valid_position(board, replace(piece, x=2, y=9))


def test_cleared_rows_compact_surviving_cells_downward() -> None:
    cells = {(x, BOARD_HEIGHT - 1): PieceType.I for x in range(BOARD_WIDTH)}
    cells[(2, BOARD_HEIGHT - 2)] = PieceType.T
    board = board_with_cells(cells)

    cleared_board, cleared = clear_full_lines(board)

    assert cleared == (BOARD_HEIGHT - 1,)
    assert cleared_board[BOARD_HEIGHT - 1][2] is PieceType.T
    assert count_filled_cells(cleared_board) == 1


def test_drop_distance_projects_piece_to_floor() -> None:
    board = empty_board()
    piece = spawn_piece(PieceType.I)

    distance = drop_distance(board, piece)
    locked, top_out = lock_piece(board, replace(piece, y=piece.y + distance))

    assert distance == 20
    assert not top_out
    assert count_filled_cells(locked, PieceType.I) == 4


def test_hidden_rows_are_reported_after_lock() -> None:
    locked, top_out = lock_piece(empty_board(), spawn_piece(PieceType.T))

    assert not top_out
    assert has_hidden_blocks(locked)
    assert any(cell is PieceType.T for row in locked[:HIDDEN_ROWS] for cell in row)
