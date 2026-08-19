from dataclasses import replace

from tetris_web.domain.board import BOARD_HEIGHT, BOARD_WIDTH, board_with_cells, drop_distance
from tetris_web.domain.engine import LOCK_DELAY_TICKS, LOCK_RESET_LIMIT, GameEngine
from tetris_web.domain.model import Command, GameStatus, PieceType, Rotation
from tetris_web.domain.scoring import gravity_interval
from tetris_web.domain.tetrominoes import spawn_piece


def test_initial_state_and_preview_are_seeded() -> None:
    first = GameEngine(seed=99)
    second = GameEngine(seed=99)

    assert first.state == second.state
    assert first.state.active is not None
    assert len(first.state.next_queue) == 5


def test_hard_drop_scores_distance_and_spawns_next_piece() -> None:
    engine = GameEngine(seed=7)
    first_kind = engine.state.active.kind
    expected_next = engine.state.next_queue[0]
    distance = engine.ghost_distance()

    engine.apply_command(Command.HARD_DROP)

    assert engine.state.score == distance * 2
    assert engine.state.pieces_placed == 1
    assert engine.state.active is not None
    assert engine.state.active.kind is expected_next
    assert any(first_kind in row for row in engine.state.board)


def test_hold_is_limited_to_once_until_piece_locks() -> None:
    engine = GameEngine(seed=123)
    first_kind = engine.state.active.kind
    expected_after_hold = engine.state.next_queue[0]

    engine.apply_command(Command.HOLD)
    state_after_first_hold = engine.state
    engine.apply_command(Command.HOLD)

    assert engine.state == state_after_first_hold
    assert engine.state.hold is first_kind
    assert engine.state.active.kind is expected_after_hold
    assert not engine.state.can_hold

    engine.apply_command(Command.HARD_DROP)
    assert engine.state.can_hold


def test_gravity_moves_on_exact_interval() -> None:
    engine = GameEngine(seed=1)
    start_y = engine.state.active.y

    for _ in range(gravity_interval(level=1) - 1):
        engine.step()
    assert engine.state.active.y == start_y

    engine.step()
    assert engine.state.active.y == start_y + 1


def test_grounded_piece_locks_after_delay() -> None:
    engine = GameEngine(seed=1)
    active = engine.state.active
    engine.state = replace(
        engine.state,
        active=replace(active, y=active.y + drop_distance(engine.state.board, active)),
    )

    for _ in range(LOCK_DELAY_TICKS - 1):
        engine.step()
    assert engine.state.pieces_placed == 0

    engine.step()
    assert engine.state.pieces_placed == 1


def test_grounded_move_resets_lock_timer_only_below_cap() -> None:
    engine = GameEngine(seed=1)
    piece = spawn_piece(PieceType.O)
    piece = replace(piece, y=piece.y + drop_distance(engine.state.board, piece))
    engine.state = replace(engine.state, active=piece, lock_ticks=12, lock_resets=3)

    engine.apply_command(Command.MOVE_LEFT)
    assert engine.state.lock_ticks == 0
    assert engine.state.lock_resets == 4

    engine.state = replace(engine.state, lock_ticks=12, lock_resets=LOCK_RESET_LIMIT)
    engine.apply_command(Command.MOVE_RIGHT)
    assert engine.state.lock_ticks == 12
    assert engine.state.lock_resets == LOCK_RESET_LIMIT


def test_locking_piece_clears_line_and_awards_points() -> None:
    engine = GameEngine(seed=1)
    gaps = set(range(3, 7))
    cells = {
        (x, BOARD_HEIGHT - 1): PieceType.J
        for x in range(BOARD_WIDTH)
        if x not in gaps
    }
    engine.state = replace(
        engine.state,
        board=board_with_cells(cells),
        active=replace(spawn_piece(PieceType.I), y=BOARD_HEIGHT - 2),
    )

    engine.apply_command(Command.HARD_DROP)

    assert engine.state.lines == 1
    assert engine.state.score == 100
    assert engine.state.last_cleared == (BOARD_HEIGHT - 1,)
    assert all(cell is None for row in engine.state.board for cell in row)


def test_piece_locking_in_hidden_rows_ends_game() -> None:
    engine = GameEngine(seed=1)
    blockers = {(4, 4): PieceType.Z, (5, 4): PieceType.Z}
    engine.state = replace(
        engine.state,
        board=board_with_cells(blockers),
        active=spawn_piece(PieceType.O),
    )

    for _ in range(LOCK_DELAY_TICKS):
        engine.step()

    assert engine.state.status is GameStatus.GAME_OVER
    assert engine.state.active is None


def test_pause_freezes_ticks_and_restart_replays_seed() -> None:
    engine = GameEngine(seed="same-opening")
    opening = engine.state

    engine.apply_command(Command.TOGGLE_PAUSE)
    engine.step()
    assert engine.state.status is GameStatus.PAUSED
    assert engine.state.tick == 0

    engine.apply_command(Command.RESTART)
    assert engine.state == opening


def test_identical_commands_produce_identical_snapshots() -> None:
    first = GameEngine(seed="recording")
    second = GameEngine(seed="recording")
    script = {
        5: Command.MOVE_LEFT,
        8: Command.ROTATE_CLOCKWISE,
        20: Command.SOFT_DROP,
        40: Command.HARD_DROP,
        55: Command.HOLD,
        80: Command.MOVE_RIGHT,
        95: Command.ROTATE_COUNTERCLOCKWISE,
        120: Command.HARD_DROP,
    }

    for tick in range(180):
        if command := script.get(tick):
            first.apply_command(command)
            second.apply_command(command)
        first.step()
        second.step()

    assert first.state == second.state
    assert first.state.active.rotation in Rotation
