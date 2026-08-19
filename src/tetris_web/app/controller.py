from __future__ import annotations

from typing import Final

from tetris_web.domain.engine import GameEngine
from tetris_web.domain.model import Command, GameStatus

DAS_TICKS: Final = 10
ARR_TICKS: Final = 2
SOFT_DROP_REPEAT_TICKS: Final = 2

DIRECTION_COMMANDS: Final = frozenset((Command.MOVE_LEFT, Command.MOVE_RIGHT))


class InputController:
    """Translate edge and held inputs into deterministic engine commands."""

    def __init__(self, engine: GameEngine) -> None:
        self.engine = engine
        self._held: set[Command] = set()
        self._active_direction: Command | None = None
        self._direction_ticks = 0
        self._soft_drop_ticks = 0

    @property
    def held_commands(self) -> frozenset[Command]:
        return frozenset(self._held)

    def press(self, command: Command) -> None:
        if command in self._held:
            return

        self._held.add(command)
        if command in DIRECTION_COMMANDS:
            self._active_direction = command
            self._direction_ticks = 0
            self.engine.apply_command(command)
        elif command is Command.SOFT_DROP:
            self._soft_drop_ticks = 0
            self.engine.apply_command(command)
        else:
            self.engine.apply_command(command)

    def release(self, command: Command) -> None:
        self._held.discard(command)
        if command is Command.SOFT_DROP:
            self._soft_drop_ticks = 0
            return

        if command is self._active_direction:
            replacement = self._other_direction(command)
            self._active_direction = replacement
            self._direction_ticks = 0
            if replacement is not None:
                self.engine.apply_command(replacement)

    def tick(self) -> None:
        if self.engine.state.status is GameStatus.PLAYING:
            self._repeat_direction()
            self._repeat_soft_drop()
        self.engine.step()

    def lose_focus(self) -> None:
        self.clear()
        if self.engine.state.status is GameStatus.PLAYING:
            self.engine.apply_command(Command.TOGGLE_PAUSE)

    def clear(self) -> None:
        self._held.clear()
        self._active_direction = None
        self._direction_ticks = 0
        self._soft_drop_ticks = 0

    def _repeat_direction(self) -> None:
        if self._active_direction is None:
            return

        self._direction_ticks += 1
        repeat_ticks = self._direction_ticks - DAS_TICKS
        if repeat_ticks >= 0 and repeat_ticks % ARR_TICKS == 0:
            self.engine.apply_command(self._active_direction)

    def _repeat_soft_drop(self) -> None:
        if Command.SOFT_DROP not in self._held:
            return

        self._soft_drop_ticks += 1
        if self._soft_drop_ticks >= SOFT_DROP_REPEAT_TICKS:
            self.engine.apply_command(Command.SOFT_DROP)
            self._soft_drop_ticks = 0

    def _other_direction(self, released: Command) -> Command | None:
        other = Command.MOVE_RIGHT if released is Command.MOVE_LEFT else Command.MOVE_LEFT
        return other if other in self._held else None
