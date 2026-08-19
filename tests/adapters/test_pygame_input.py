import pygame

from tetris_web.adapters.pygame_audio import PygameAudio
from tetris_web.adapters.pygame_input import PygameInput
from tetris_web.adapters.pygame_renderer import build_layout
from tetris_web.app.controller import InputController
from tetris_web.domain.engine import GameEngine
from tetris_web.domain.model import Command, GameStatus


def create_input() -> tuple[PygameInput, InputController, PygameAudio]:
    controller = InputController(GameEngine(seed=9))
    audio = PygameAudio()
    return PygameInput(controller, audio), controller, audio


def test_keyboard_events_press_and_release_commands() -> None:
    adapter, controller, _ = create_input()
    layout = build_layout((1000, 720))
    start_x = controller.engine.state.active.x

    adapter.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT), layout)
    assert controller.engine.state.active.x == start_x - 1
    assert Command.MOVE_LEFT in controller.held_commands

    adapter.handle(pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT), layout)
    assert Command.MOVE_LEFT not in controller.held_commands


def test_pointer_button_uses_same_controller_path() -> None:
    adapter, controller, _ = create_input()
    layout = build_layout((390, 844))
    button = layout.command_buttons[Command.MOVE_RIGHT]
    start_x = controller.engine.state.active.x

    adapter.handle(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=button.center), layout
    )
    assert controller.engine.state.active.x == start_x + 1
    assert Command.MOVE_RIGHT in controller.held_commands

    adapter.handle(
        pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=button.center), layout
    )
    assert Command.MOVE_RIGHT not in controller.held_commands


def test_touch_coordinates_are_scaled_to_surface() -> None:
    adapter, controller, _ = create_input()
    layout = build_layout((390, 844))
    button = layout.command_buttons[Command.SOFT_DROP]
    start_score = controller.engine.state.score

    adapter.handle(
        pygame.event.Event(
            pygame.FINGERDOWN,
            finger_id=3,
            x=button.centerx / layout.screen.width,
            y=button.centery / layout.screen.height,
        ),
        layout,
    )

    assert controller.engine.state.score == start_score + 1


def test_focus_loss_pauses_and_releases_inputs() -> None:
    adapter, controller, _ = create_input()
    layout = build_layout((1000, 720))
    adapter.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN), layout)

    adapter.handle(pygame.event.Event(pygame.WINDOWFOCUSLOST), layout)

    assert controller.engine.state.status is GameStatus.PAUSED
    assert not controller.held_commands


def test_mute_button_toggles_audio_state() -> None:
    adapter, _, audio = create_input()
    layout = build_layout((390, 844))

    adapter.handle(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=layout.mute_button.center,
        ),
        layout,
    )

    assert audio.muted
