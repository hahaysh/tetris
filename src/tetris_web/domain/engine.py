from __future__ import annotations

from dataclasses import replace
from typing import Final

from tetris_web.domain.board import (
    clear_full_lines,
    drop_distance,
    empty_board,
    has_hidden_blocks,
    is_valid_position,
    lock_piece,
    move_piece,
    rotate_piece,
)
from tetris_web.domain.model import ActivePiece, Command, GameState, GameStatus, PieceType, Seed
from tetris_web.domain.randomizer import SevenBag
from tetris_web.domain.scoring import gravity_interval, level_for_lines, line_clear_points
from tetris_web.domain.tetrominoes import spawn_piece

TICKS_PER_SECOND: Final = 60
PREVIEW_SIZE: Final = 5
LOCK_DELAY_TICKS: Final = 30
LOCK_RESET_LIMIT: Final = 15


class GameEngine:
    """Own deterministic game state and advance it in fixed simulation ticks."""

    def __init__(self, seed: Seed = None) -> None:
        self._seed = seed
        self._bag = SevenBag(seed)
        self.state = self._create_initial_state()

    def restart(self) -> GameState:
        self._bag = SevenBag(self._seed)
        self.state = self._create_initial_state()
        return self.state

    def apply_command(self, command: Command) -> GameState:
        if command is Command.RESTART:
            return self.restart()

        if command is Command.TOGGLE_PAUSE:
            if self.state.status is GameStatus.PLAYING:
                self.state = replace(self.state, status=GameStatus.PAUSED)
            elif self.state.status is GameStatus.PAUSED:
                self.state = replace(self.state, status=GameStatus.PLAYING)
            return self.state

        if self.state.status is not GameStatus.PLAYING or self.state.active is None:
            return self.state

        handlers = {
            Command.MOVE_LEFT: lambda: self._move_horizontal(-1),
            Command.MOVE_RIGHT: lambda: self._move_horizontal(1),
            Command.SOFT_DROP: self._soft_drop,
            Command.HARD_DROP: self._hard_drop,
            Command.ROTATE_CLOCKWISE: lambda: self._rotate(1),
            Command.ROTATE_COUNTERCLOCKWISE: lambda: self._rotate(-1),
            Command.HOLD: self._hold,
        }
        handler = handlers.get(command)
        if handler is not None:
            handler()
        return self.state

    def step(self) -> GameState:
        if self.state.status is not GameStatus.PLAYING or self.state.active is None:
            return self.state

        self.state = replace(self.state, tick=self.state.tick + 1, last_cleared=())
        active = self.state.active
        downward = move_piece(self.state.board, active, 0, 1)

        if downward is None:
            lock_ticks = self.state.lock_ticks + 1
            if lock_ticks >= LOCK_DELAY_TICKS:
                self._lock_active()
            else:
                self.state = replace(self.state, lock_ticks=lock_ticks)
            return self.state

        gravity_ticks = self.state.gravity_ticks + 1
        if gravity_ticks >= gravity_interval(self.state.level):
            self.state = replace(
                self.state,
                active=downward,
                gravity_ticks=0,
                lock_ticks=0,
            )
        else:
            self.state = replace(self.state, gravity_ticks=gravity_ticks)
        return self.state

    def ghost_distance(self) -> int:
        if self.state.active is None:
            return 0
        return drop_distance(self.state.board, self.state.active)

    def _create_initial_state(self) -> GameState:
        first = self._bag.next_piece()
        queue = tuple(self._bag.next_piece() for _ in range(PREVIEW_SIZE))
        active = spawn_piece(first)
        return GameState(
            board=empty_board(),
            active=active,
            hold=None,
            next_queue=queue,
            status=GameStatus.PLAYING,
            score=0,
            lines=0,
            level=1,
            tick=0,
            gravity_ticks=0,
            lock_ticks=0,
            lock_resets=0,
            can_hold=True,
            pieces_placed=0,
            last_cleared=(),
        )

    def _move_horizontal(self, dx: int) -> None:
        active = self._require_active()
        candidate = move_piece(self.state.board, active, dx, 0)
        if candidate is not None:
            self._commit_manipulation(candidate)

    def _soft_drop(self) -> None:
        active = self._require_active()
        candidate = move_piece(self.state.board, active, 0, 1)
        if candidate is not None:
            self.state = replace(
                self.state,
                active=candidate,
                score=self.state.score + 1,
                gravity_ticks=0,
                lock_ticks=0,
            )

    def _hard_drop(self) -> None:
        active = self._require_active()
        distance = drop_distance(self.state.board, active)
        self.state = replace(
            self.state,
            active=replace(active, y=active.y + distance),
            score=self.state.score + distance * 2,
        )
        self._lock_active()

    def _rotate(self, direction: int) -> None:
        active = self._require_active()
        candidate = rotate_piece(self.state.board, active, direction)
        if candidate != active:
            self._commit_manipulation(candidate)

    def _commit_manipulation(self, candidate: ActivePiece) -> None:
        active = self._require_active()
        was_grounded = move_piece(self.state.board, active, 0, 1) is None
        updates: dict[str, object] = {"active": candidate}
        if was_grounded and self.state.lock_resets < LOCK_RESET_LIMIT:
            updates["lock_ticks"] = 0
            updates["lock_resets"] = self.state.lock_resets + 1
        elif not was_grounded:
            updates["lock_ticks"] = 0
        self.state = replace(self.state, **updates)

    def _hold(self) -> None:
        if not self.state.can_hold:
            return

        active = self._require_active()
        if self.state.hold is None:
            next_kind, queue = self._take_next_piece()
        else:
            next_kind = self.state.hold
            queue = self.state.next_queue

        candidate = spawn_piece(next_kind)
        if not is_valid_position(self.state.board, candidate):
            self.state = replace(
                self.state,
                active=None,
                hold=active.kind,
                next_queue=queue,
                can_hold=False,
                status=GameStatus.GAME_OVER,
            )
            return

        self.state = replace(
            self.state,
            active=candidate,
            hold=active.kind,
            next_queue=queue,
            can_hold=False,
            gravity_ticks=0,
            lock_ticks=0,
            lock_resets=0,
        )

    def _lock_active(self) -> None:
        active = self._require_active()
        locked_board, above_board = lock_piece(self.state.board, active)
        cleared_board, cleared_rows = clear_full_lines(locked_board)
        total_lines = self.state.lines + len(cleared_rows)
        score = self.state.score + line_clear_points(len(cleared_rows), self.state.level)

        base_state = replace(
            self.state,
            board=cleared_board,
            active=None,
            score=score,
            lines=total_lines,
            level=level_for_lines(total_lines),
            pieces_placed=self.state.pieces_placed + 1,
            last_cleared=cleared_rows,
            gravity_ticks=0,
            lock_ticks=0,
            lock_resets=0,
        )
        self.state = base_state

        if above_board or has_hidden_blocks(cleared_board):
            self.state = replace(self.state, status=GameStatus.GAME_OVER)
            return

        next_kind, queue = self._take_next_piece()
        candidate = spawn_piece(next_kind)
        if not is_valid_position(cleared_board, candidate):
            self.state = replace(
                self.state,
                next_queue=queue,
                status=GameStatus.GAME_OVER,
            )
            return

        self.state = replace(
            self.state,
            active=candidate,
            next_queue=queue,
            can_hold=True,
        )

    def _take_next_piece(self) -> tuple[PieceType, tuple[PieceType, ...]]:
        next_kind = self.state.next_queue[0]
        queue = (*self.state.next_queue[1:], self._bag.next_piece())
        return next_kind, queue

    def _require_active(self) -> ActivePiece:
        active = self.state.active
        if active is None:
            raise RuntimeError("game has no active piece")
        return active
