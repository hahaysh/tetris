from __future__ import annotations

from typing import Final

import pygame

from tetris_web.adapters.pygame_audio import PygameAudio
from tetris_web.adapters.pygame_renderer import Layout
from tetris_web.app.controller import InputController
from tetris_web.domain.model import Command

type ControlTarget = Command | str

KEY_COMMANDS: Final[dict[int, Command]] = {
    pygame.K_LEFT: Command.MOVE_LEFT,
    pygame.K_a: Command.MOVE_LEFT,
    pygame.K_RIGHT: Command.MOVE_RIGHT,
    pygame.K_d: Command.MOVE_RIGHT,
    pygame.K_DOWN: Command.SOFT_DROP,
    pygame.K_s: Command.SOFT_DROP,
    pygame.K_SPACE: Command.HARD_DROP,
    pygame.K_UP: Command.ROTATE_CLOCKWISE,
    pygame.K_x: Command.ROTATE_CLOCKWISE,
    pygame.K_w: Command.ROTATE_CLOCKWISE,
    pygame.K_z: Command.ROTATE_COUNTERCLOCKWISE,
    pygame.K_q: Command.ROTATE_COUNTERCLOCKWISE,
    pygame.K_c: Command.HOLD,
    pygame.K_LSHIFT: Command.HOLD,
    pygame.K_RSHIFT: Command.HOLD,
    pygame.K_p: Command.TOGGLE_PAUSE,
    pygame.K_ESCAPE: Command.TOGGLE_PAUSE,
    pygame.K_r: Command.RESTART,
}


class PygameInput:
    def __init__(self, controller: InputController, audio: PygameAudio) -> None:
        self.controller = controller
        self.audio = audio
        self._mouse_target: ControlTarget | None = None
        self._finger_targets: dict[int, ControlTarget] = {}

    def handle(self, event: pygame.event.Event, layout: Layout) -> bool:
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.WINDOWFOCUSLOST:
            self.controller.lose_focus()
            self._mouse_target = None
            self._finger_targets.clear()
        elif event.type == pygame.KEYDOWN:
            if command := KEY_COMMANDS.get(event.key):
                self._press(command)
        elif event.type == pygame.KEYUP:
            if command := KEY_COMMANDS.get(event.key):
                self.controller.release(command)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not getattr(event, "touch", False):
                self._mouse_target = self._target_at(event.pos, layout)
                self._press_target(self._mouse_target)
        elif event.type == pygame.MOUSEMOTION and self._mouse_target is not None:
            if not getattr(event, "touch", False):
                self._update_pointer_target(event.pos, layout, mouse=True)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not getattr(event, "touch", False):
                self._release_target(self._mouse_target)
                self._mouse_target = None
        elif event.type == pygame.FINGERDOWN:
            position = self._finger_position(event, layout)
            target = self._target_at(position, layout)
            if target is not None:
                self._finger_targets[event.finger_id] = target
                self._press_target(target)
        elif event.type == pygame.FINGERMOTION and event.finger_id in self._finger_targets:
            position = self._finger_position(event, layout)
            self._update_pointer_target(position, layout, finger_id=event.finger_id)
        elif event.type == pygame.FINGERUP:
            target = self._finger_targets.pop(event.finger_id, None)
            self._release_target(target)
        return False

    def _press(self, command: Command) -> None:
        self.controller.press(command)
        self.audio.play_command(command)

    def _press_target(self, target: ControlTarget | None) -> None:
        if isinstance(target, Command):
            self._press(target)
        elif target == "mute":
            self.audio.toggle_mute()

    def _release_target(self, target: ControlTarget | None) -> None:
        if isinstance(target, Command):
            self.controller.release(target)

    def _update_pointer_target(
        self,
        position: tuple[int, int],
        layout: Layout,
        *,
        mouse: bool = False,
        finger_id: int | None = None,
    ) -> None:
        previous = self._mouse_target if mouse else self._finger_targets.get(finger_id)
        current = self._target_at(position, layout)
        if current == previous:
            return
        self._release_target(previous)
        self._press_target(current)
        if mouse:
            self._mouse_target = current
        elif finger_id is not None:
            if current is None:
                self._finger_targets.pop(finger_id, None)
            else:
                self._finger_targets[finger_id] = current

    @staticmethod
    def _target_at(position: tuple[int, int], layout: Layout) -> ControlTarget | None:
        if layout.mute_button.collidepoint(position):
            return "mute"
        return next(
            (
                command
                for command, rect in layout.command_buttons.items()
                if rect.collidepoint(position)
            ),
            None,
        )

    @staticmethod
    def _finger_position(event: pygame.event.Event, layout: Layout) -> tuple[int, int]:
        return (
            round(event.x * layout.screen.width),
            round(event.y * layout.screen.height),
        )
