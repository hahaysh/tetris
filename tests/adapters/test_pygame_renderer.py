from dataclasses import replace

import pygame
import pytest

from tetris_web.adapters.pygame_renderer import PygameRenderer, build_layout
from tetris_web.domain.engine import GameEngine
from tetris_web.domain.model import Command
from tetris_web.domain.tetrominoes import absolute_cells


@pytest.mark.parametrize(("size", "portrait"), [((1000, 720), False), ((390, 844), True)])
def test_layout_keeps_board_and_controls_inside_viewport(
    size: tuple[int, int], portrait: bool
) -> None:
    layout = build_layout(size)

    assert layout.portrait is portrait
    assert layout.board.width == layout.cell_size * 10
    assert layout.board.height == layout.cell_size * 20
    assert layout.screen.contains(layout.board)
    assert layout.screen.contains(layout.hold)
    assert all(layout.screen.contains(rect) for rect in layout.next_previews)
    assert all(layout.screen.contains(rect) for rect in layout.command_buttons.values())
    assert layout.screen.contains(layout.mute_button)
    assert not any(layout.board.colliderect(rect) for rect in layout.command_buttons.values())


def test_renderer_produces_nonblank_surface() -> None:
    pygame.font.init()
    surface = pygame.Surface((1000, 720))
    engine = GameEngine(seed=2026)
    engine.state = replace(engine.state, active=replace(engine.state.active, y=6))

    layout = PygameRenderer().draw(surface, engine.state, engine.ghost_distance())
    active_x, active_y = absolute_cells(engine.state.active)[0]
    block_center = (
        layout.board.left + active_x * layout.cell_size + layout.cell_size // 2,
        layout.board.top + (active_y - 4) * layout.cell_size + layout.cell_size // 2,
    )
    button = layout.command_buttons[Command.MOVE_LEFT]

    sample_points = [
        (0, 0),
        (layout.board.left + 3, layout.board.top + 3),
        (layout.board.left + layout.cell_size, layout.board.top + layout.cell_size),
        (button.left + 3, button.top + 3),
        block_center,
    ]
    assert len({tuple(surface.get_at(point)) for point in sample_points}) >= 4
