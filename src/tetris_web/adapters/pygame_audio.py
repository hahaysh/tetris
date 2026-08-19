from __future__ import annotations

import math
from array import array
from typing import Final

import pygame

from tetris_web.domain.model import Command, GameState, GameStatus

SAMPLE_RATE: Final = 22_050


class PygameAudio:
    """Generate small original sound effects after the first user interaction."""

    def __init__(self) -> None:
        self.muted = False
        self._initialized = False
        self._available = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}

    def toggle_mute(self) -> None:
        self.muted = not self.muted

    def play_command(self, command: Command) -> None:
        sound_name = {
            Command.MOVE_LEFT: "move",
            Command.MOVE_RIGHT: "move",
            Command.SOFT_DROP: "move",
            Command.ROTATE_CLOCKWISE: "rotate",
            Command.ROTATE_COUNTERCLOCKWISE: "rotate",
            Command.HARD_DROP: "drop",
            Command.HOLD: "hold",
        }.get(command)
        if sound_name:
            self._play(sound_name)

    def sync_state(self, previous: GameState, current: GameState) -> None:
        if current.status is GameStatus.GAME_OVER and previous.status is not GameStatus.GAME_OVER:
            self._play("game_over")
        elif current.last_cleared and not previous.last_cleared:
            self._play("line")
        elif current.pieces_placed > previous.pieces_placed:
            self._play("lock")

    def _play(self, name: str) -> None:
        if self.muted or not self._ensure_initialized():
            return
        self._sounds[name].play()

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return self._available
        self._initialized = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=256)
            self._sounds = {
                "move": self._tone(180, 0.025, 0.08),
                "rotate": self._tone(320, 0.04, 0.1),
                "drop": self._tone(105, 0.08, 0.16),
                "hold": self._tone(420, 0.055, 0.1),
                "lock": self._tone(135, 0.035, 0.1),
                "line": self._tone(660, 0.13, 0.15),
                "game_over": self._tone(82, 0.3, 0.18),
            }
        except pygame.error:
            self._available = False
        return self._available

    @staticmethod
    def _tone(frequency: float, duration: float, volume: float) -> pygame.mixer.Sound:
        sample_count = max(1, round(SAMPLE_RATE * duration))
        samples = array("h")
        for index in range(sample_count):
            progress = index / sample_count
            envelope = (1 - progress) ** 2
            sample = math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
            samples.append(round(32_767 * volume * envelope * sample))
        return pygame.mixer.Sound(buffer=samples.tobytes())
