from tetris_web.app.controller import ARR_TICKS, DAS_TICKS, InputController
from tetris_web.domain.engine import GameEngine
from tetris_web.domain.model import Command, GameStatus


def active_x(controller: InputController) -> int:
    assert controller.engine.state.active is not None
    return controller.engine.state.active.x


def test_direction_moves_immediately_then_repeats_after_das() -> None:
    controller = InputController(GameEngine(seed=4))
    start_x = active_x(controller)

    controller.press(Command.MOVE_LEFT)
    assert active_x(controller) == start_x - 1

    for _ in range(DAS_TICKS - 1):
        controller.tick()
    assert active_x(controller) == start_x - 1

    controller.tick()
    assert active_x(controller) == start_x - 2

    for _ in range(ARR_TICKS):
        controller.tick()
    assert active_x(controller) == start_x - 3


def test_releasing_latest_direction_resumes_other_direction() -> None:
    controller = InputController(GameEngine(seed=4))
    start_x = active_x(controller)

    controller.press(Command.MOVE_LEFT)
    controller.press(Command.MOVE_RIGHT)
    assert active_x(controller) == start_x

    controller.release(Command.MOVE_RIGHT)
    assert active_x(controller) == start_x - 1


def test_repeated_keydown_does_not_repeat_edge_command() -> None:
    controller = InputController(GameEngine(seed=4))

    controller.press(Command.HARD_DROP)
    controller.press(Command.HARD_DROP)

    assert controller.engine.state.pieces_placed == 1

    controller.release(Command.HARD_DROP)
    controller.press(Command.HARD_DROP)
    assert controller.engine.state.pieces_placed == 2


def test_held_soft_drop_repeats_in_simulation_ticks() -> None:
    controller = InputController(GameEngine(seed=4))

    controller.press(Command.SOFT_DROP)
    for _ in range(4):
        controller.tick()

    assert controller.engine.state.score == 3


def test_focus_loss_clears_inputs_and_pauses_game() -> None:
    controller = InputController(GameEngine(seed=4))
    controller.press(Command.MOVE_LEFT)
    controller.press(Command.SOFT_DROP)

    controller.lose_focus()

    assert controller.engine.state.status is GameStatus.PAUSED
    assert not controller.held_commands


def test_paused_game_does_not_advance_engine_tick() -> None:
    controller = InputController(GameEngine(seed=4))
    controller.press(Command.TOGGLE_PAUSE)
    controller.release(Command.TOGGLE_PAUSE)

    for _ in range(20):
        controller.tick()

    assert controller.engine.state.tick == 0
