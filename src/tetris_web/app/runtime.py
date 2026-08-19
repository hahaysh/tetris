from __future__ import annotations

import asyncio
import os
from typing import Final

import pygame

from tetris_web.adapters.pygame_audio import PygameAudio
from tetris_web.adapters.pygame_input import PygameInput
from tetris_web.adapters.pygame_renderer import PygameRenderer, build_layout
from tetris_web.app.controller import InputController
from tetris_web.domain.engine import TICKS_PER_SECOND, GameEngine

INITIAL_SIZE: Final = (1000, 720)
MINIMUM_SIZE: Final = (320, 480)
MAX_FRAME_SECONDS: Final = 0.25


async def run() -> None:
    pygame.init()
    pygame.display.set_caption("Stackline")
    screen = pygame.display.set_mode(INITIAL_SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()

    engine = GameEngine()
    controller = InputController(engine)
    renderer = PygameRenderer()
    audio = PygameAudio()
    input_adapter = PygameInput(controller, audio)
    layout = build_layout(screen.get_size())

    fixed_step = 1 / TICKS_PER_SECOND
    accumulator = 0.0
    running = True
    rendered_frames = 0
    smoke_frames = int(os.environ.get("STACKLINE_SMOKE_FRAMES", "0"))

    while running:
        frame_seconds = min(clock.tick(120) / 1000, MAX_FRAME_SECONDS)
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                width = max(MINIMUM_SIZE[0], event.w)
                height = max(MINIMUM_SIZE[1], event.h)
                screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                layout = build_layout(screen.get_size())
            elif input_adapter.handle(event, layout):
                running = False

        accumulator += frame_seconds
        while accumulator >= fixed_step:
            previous = engine.state
            controller.tick()
            audio.sync_state(previous, engine.state)
            accumulator -= fixed_step

        layout = renderer.draw(
            screen,
            engine.state,
            engine.ghost_distance(),
            controller.held_commands,
            audio.muted,
        )
        pygame.display.flip()
        rendered_frames += 1
        if smoke_frames and rendered_frames >= smoke_frames:
            running = False
        await asyncio.sleep(0)

    pygame.quit()
