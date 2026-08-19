from __future__ import annotations

from dataclasses import dataclass, replace
from math import pi
from typing import Final

import pygame

from tetris_web.domain.board import BOARD_WIDTH, HIDDEN_ROWS, VISIBLE_HEIGHT
from tetris_web.domain.model import Command, GameState, GameStatus, PieceType
from tetris_web.domain.tetrominoes import absolute_cells, local_cells

Color = tuple[int, int, int]

BACKGROUND: Final[Color] = (15, 17, 15)
BACKGROUND_PATTERN: Final[Color] = (24, 27, 23)
WELL: Final[Color] = (7, 9, 8)
GRID: Final[Color] = (27, 31, 28)
TEXT: Final[Color] = (241, 238, 226)
MUTED: Final[Color] = (139, 146, 136)
CORAL: Final[Color] = (248, 104, 91)
LIME: Final[Color] = (183, 224, 83)
BUTTON: Final[Color] = (36, 40, 36)
BUTTON_ACTIVE: Final[Color] = (66, 74, 61)

PIECE_COLORS: Final[dict[PieceType, Color]] = {
    PieceType.I: (69, 205, 221),
    PieceType.J: (79, 116, 226),
    PieceType.L: (239, 151, 62),
    PieceType.O: (238, 205, 76),
    PieceType.S: (102, 190, 95),
    PieceType.T: (184, 101, 205),
    PieceType.Z: (232, 82, 91),
}

PORTRAIT_COMMANDS: Final[tuple[tuple[Command, ...], ...]] = (
    (
        Command.MOVE_LEFT,
        Command.SOFT_DROP,
        Command.MOVE_RIGHT,
        Command.HARD_DROP,
        Command.HOLD,
    ),
    (
        Command.ROTATE_COUNTERCLOCKWISE,
        Command.ROTATE_CLOCKWISE,
        Command.TOGGLE_PAUSE,
        Command.RESTART,
    ),
)


@dataclass(frozen=True, slots=True)
class Layout:
    screen: pygame.Rect
    board: pygame.Rect
    cell_size: int
    hold: pygame.Rect
    next_previews: tuple[pygame.Rect, ...]
    command_buttons: dict[Command, pygame.Rect]
    mute_button: pygame.Rect
    portrait: bool


def build_layout(size: tuple[int, int]) -> Layout:
    width, height = size
    screen = pygame.Rect(0, 0, width, height)
    portrait = height > width * 1.05 or width < 700

    if portrait:
        toolbar_height = 72
        control_height = min(180, max(132, int(height * 0.21)))
        available_height = max(200, height - toolbar_height - control_height - 12)
        cell_size = max(10, min((width - 32) // BOARD_WIDTH, available_height // VISIBLE_HEIGHT))
        board = pygame.Rect(
            (width - cell_size * BOARD_WIDTH) // 2,
            toolbar_height + max(0, (available_height - cell_size * VISIBLE_HEIGHT) // 2),
            cell_size * BOARD_WIDTH,
            cell_size * VISIBLE_HEIGHT,
        )

        preview_size = min(48, max(34, width // 9))
        hold = pygame.Rect(12, 12, preview_size, preview_size)
        next_previews = (pygame.Rect(width - preview_size - 12, 12, preview_size, preview_size),)

        controls_top = board.bottom + 8
        controls_height = max(80, height - controls_top - 8)
        gap = max(5, min(9, width // 55))
        button_size = min(54, (width - 32 - gap * 4) // 5, (controls_height - gap) // 2)
        button_size = max(32, button_size)
        row_width = button_size * 5 + gap * 4
        row_x = (width - row_width) // 2
        grid_height = button_size * 2 + gap
        row_y = controls_top + max(0, (controls_height - grid_height) // 2)

        command_buttons: dict[Command, pygame.Rect] = {}
        for column, command in enumerate(PORTRAIT_COMMANDS[0]):
            command_buttons[command] = pygame.Rect(
                row_x + column * (button_size + gap), row_y, button_size, button_size
            )
        for column, command in enumerate(PORTRAIT_COMMANDS[1]):
            command_buttons[command] = pygame.Rect(
                row_x + column * (button_size + gap),
                row_y + button_size + gap,
                button_size,
                button_size,
            )
        mute_button = pygame.Rect(
            row_x + 4 * (button_size + gap),
            row_y + button_size + gap,
            button_size,
            button_size,
        )
    else:
        margin = max(22, min(38, width // 35))
        side_space = max(190, min(280, width // 4))
        cell_size = max(
            12,
            min(
                (height - margin * 2) // VISIBLE_HEIGHT,
                (width - side_space * 2) // BOARD_WIDTH,
            ),
        )
        board = pygame.Rect(
            (width - cell_size * BOARD_WIDTH) // 2,
            (height - cell_size * VISIBLE_HEIGHT) // 2,
            cell_size * BOARD_WIDTH,
            cell_size * VISIBLE_HEIGHT,
        )
        left_width = board.left - margin * 2
        right_x = board.right + margin
        right_width = width - right_x - margin
        preview_size = min(128, max(84, left_width))
        hold = pygame.Rect(
            margin,
            board.top + 92,
            min(preview_size, left_width),
            min(104, preview_size),
        )
        next_size = min(86, max(58, right_width))
        next_previews = tuple(
            pygame.Rect(right_x, board.top + 82 + index * (next_size + 12), next_size, next_size)
            for index in range(3)
        )

        button_size = min(52, max(38, left_width // 3 - 6))
        gap = 7
        movement_width = button_size * 3 + gap * 2
        movement_x = margin + max(0, (left_width - movement_width) // 2)
        movement_y = min(height - margin - button_size, board.bottom - button_size)
        command_buttons = {
            Command.MOVE_LEFT: pygame.Rect(movement_x, movement_y, button_size, button_size),
            Command.SOFT_DROP: pygame.Rect(
                movement_x + button_size + gap, movement_y, button_size, button_size
            ),
            Command.MOVE_RIGHT: pygame.Rect(
                movement_x + (button_size + gap) * 2,
                movement_y,
                button_size,
                button_size,
            ),
        }

        action_size = min(48, max(36, right_width // 2 - 5))
        action_gap = 7
        action_x = right_x
        action_y = board.bottom - action_size * 2 - action_gap
        for index, command in enumerate(
            (
                Command.HOLD,
                Command.HARD_DROP,
                Command.ROTATE_COUNTERCLOCKWISE,
                Command.ROTATE_CLOCKWISE,
            )
        ):
            column = index % 2
            row = index // 2
            command_buttons[command] = pygame.Rect(
                action_x + column * (action_size + action_gap),
                action_y + row * (action_size + action_gap),
                action_size,
                action_size,
            )

        utility_size = 38
        utility_y = margin
        mute_button = pygame.Rect(
            width - margin - utility_size, utility_y, utility_size, utility_size
        )
        command_buttons[Command.RESTART] = pygame.Rect(
            mute_button.left - utility_size - 7, utility_y, utility_size, utility_size
        )
        command_buttons[Command.TOGGLE_PAUSE] = pygame.Rect(
            mute_button.left - (utility_size + 7) * 2,
            utility_y,
            utility_size,
            utility_size,
        )

    return Layout(
        screen=screen,
        board=board,
        cell_size=cell_size,
        hold=hold,
        next_previews=next_previews,
        command_buttons=command_buttons,
        mute_button=mute_button,
        portrait=portrait,
    )


class PygameRenderer:
    def __init__(self) -> None:
        pygame.font.init()
        self._fonts: dict[int, pygame.font.Font] = {}
        self._flash_rows: tuple[int, ...] = ()
        self._flash_until = 0

    def draw(
        self,
        surface: pygame.Surface,
        state: GameState,
        ghost_distance: int,
        held_commands: frozenset[Command] = frozenset(),
        muted: bool = False,
    ) -> Layout:
        layout = build_layout(surface.get_size())
        self._draw_background(surface)
        self._draw_board(surface, layout, state, ghost_distance)

        if layout.portrait:
            self._draw_portrait_header(surface, layout, state)
        else:
            self._draw_landscape_panels(surface, layout, state)

        for command, rect in layout.command_buttons.items():
            self._draw_button(surface, rect, command, command in held_commands, muted)
        self._draw_button(surface, layout.mute_button, "mute", False, muted)
        self._draw_status_overlay(surface, layout, state)
        return layout

    def _draw_background(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND)
        width, height = surface.get_size()
        for y in range(14, height, 28):
            offset = 14 if (y // 28) % 2 else 0
            for x in range(offset, width, 28):
                pygame.draw.circle(surface, BACKGROUND_PATTERN, (x, y), 1)

    def _draw_board(
        self,
        surface: pygame.Surface,
        layout: Layout,
        state: GameState,
        ghost_distance: int,
    ) -> None:
        board = layout.board
        cell_size = layout.cell_size
        pygame.draw.rect(surface, WELL, board)
        pygame.draw.rect(surface, (67, 74, 66), board, width=2)

        for column in range(1, BOARD_WIDTH):
            x = board.left + column * cell_size
            pygame.draw.line(surface, GRID, (x, board.top), (x, board.bottom))
        for row in range(1, VISIBLE_HEIGHT):
            y = board.top + row * cell_size
            pygame.draw.line(surface, GRID, (board.left, y), (board.right, y))

        for board_y, row in enumerate(state.board[HIDDEN_ROWS:], start=HIDDEN_ROWS):
            for x, kind in enumerate(row):
                if kind is not None:
                    self._draw_block(surface, self._cell_rect(layout, x, board_y), kind)

        if state.active is not None:
            if ghost_distance > 0:
                ghost = replace(state.active, y=state.active.y + ghost_distance)
                for x, y in absolute_cells(ghost):
                    if y >= HIDDEN_ROWS:
                        self._draw_ghost(surface, self._cell_rect(layout, x, y), ghost.kind)
            for x, y in absolute_cells(state.active):
                if y >= HIDDEN_ROWS:
                    self._draw_block(surface, self._cell_rect(layout, x, y), state.active.kind)

        if state.last_cleared:
            self._flash_rows = state.last_cleared
            self._flash_until = pygame.time.get_ticks() + 150
        if pygame.time.get_ticks() < self._flash_until:
            flash = pygame.Surface((board.width, cell_size), pygame.SRCALPHA)
            flash.fill((*TEXT, 145))
            for row in self._flash_rows:
                if row >= HIDDEN_ROWS:
                    surface.blit(flash, (board.left, board.top + (row - HIDDEN_ROWS) * cell_size))

    def _draw_portrait_header(
        self, surface: pygame.Surface, layout: Layout, state: GameState
    ) -> None:
        self._draw_preview(surface, layout.hold, state.hold, "HOLD")
        next_kind = state.next_queue[0] if state.next_queue else None
        self._draw_preview(surface, layout.next_previews[0], next_kind, "NEXT")
        self._text(surface, "STACKLINE", 24, TEXT, (layout.screen.centerx, 20), "midtop")
        metric = f"{state.score:07d}  /  L{state.level:02d}"
        self._text(surface, metric, 15, MUTED, (layout.screen.centerx, 49), "midtop")

    def _draw_landscape_panels(
        self, surface: pygame.Surface, layout: Layout, state: GameState
    ) -> None:
        margin = max(22, min(38, layout.screen.width // 35))
        self._text(surface, "STACKLINE", 32, TEXT, (margin, layout.board.top), "topleft")
        self._text(
            surface,
            "PRECISION FALLING BLOCKS",
            12,
            MUTED,
            (margin, layout.board.top + 42),
            "topleft",
        )
        self._draw_preview(surface, layout.hold, state.hold, "HOLD")

        right_x = layout.next_previews[0].left
        self._text(surface, "NEXT", 12, MUTED, (right_x, layout.board.top + 55), "topleft")
        for rect, kind in zip(layout.next_previews, state.next_queue, strict=False):
            self._draw_preview(surface, rect, kind)

        metrics_y = layout.board.top + 82 + len(layout.next_previews) * (
            layout.next_previews[0].height + 12
        )
        self._text(surface, "SCORE", 12, MUTED, (right_x, metrics_y), "topleft")
        self._text(surface, f"{state.score:07d}", 23, TEXT, (right_x, metrics_y + 18), "topleft")
        self._text(surface, "LINES", 12, MUTED, (right_x, metrics_y + 57), "topleft")
        self._text(surface, f"{state.lines:03d}", 23, TEXT, (right_x, metrics_y + 75), "topleft")
        self._text(surface, "LEVEL", 12, MUTED, (right_x + 76, metrics_y + 57), "topleft")
        self._text(
            surface,
            f"{state.level:02d}",
            23,
            LIME,
            (right_x + 76, metrics_y + 75),
            "topleft",
        )

    def _draw_preview(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        kind: PieceType | None,
        label: str | None = None,
    ) -> None:
        pygame.draw.rect(surface, (25, 29, 25), rect, border_radius=6)
        pygame.draw.rect(surface, (55, 62, 54), rect, width=1, border_radius=6)
        if label:
            self._text(surface, label, 10, MUTED, (rect.centerx, rect.top + 5), "midtop")
        if kind is None:
            return

        cells = local_cells(kind, rotation=0)  # Rotation.SPAWN is numerically zero.
        min_x = min(x for x, _ in cells)
        max_x = max(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        max_y = max(y for _, y in cells)
        piece_width = max_x - min_x + 1
        piece_height = max_y - min_y + 1
        top_padding = 10 if label else 0
        block_size = max(
            5,
            min(
                (rect.width - 18) // piece_width,
                (rect.height - 18 - top_padding) // piece_height,
            ),
        )
        origin_x = rect.centerx - piece_width * block_size // 2
        origin_y = rect.centery - piece_height * block_size // 2 + top_padding // 2
        for x, y in cells:
            block = pygame.Rect(
                origin_x + (x - min_x) * block_size,
                origin_y + (y - min_y) * block_size,
                block_size,
                block_size,
            )
            self._draw_block(surface, block, kind)

    def _draw_block(
        self, surface: pygame.Surface, rect: pygame.Rect, kind: PieceType
    ) -> None:
        block = rect.inflate(-max(1, rect.width // 13), -max(1, rect.height // 13))
        color = PIECE_COLORS[kind]
        radius = max(2, block.width // 7)
        pygame.draw.rect(surface, self._shade(color, 0.55), block, border_radius=radius)
        inset = max(2, block.width // 9)
        face = block.inflate(-inset, -inset)
        pygame.draw.rect(surface, color, face, border_radius=max(1, radius - 1))
        highlight = self._shade(color, 1.28)
        pygame.draw.line(
            surface,
            highlight,
            (face.left + 2, face.top + 2),
            (face.right - 3, face.top + 2),
            max(1, block.width // 14),
        )
        pygame.draw.line(
            surface,
            highlight,
            (face.left + 2, face.top + 2),
            (face.left + 2, face.bottom - 3),
            max(1, block.width // 14),
        )

    def _draw_ghost(
        self, surface: pygame.Surface, rect: pygame.Rect, kind: PieceType
    ) -> None:
        ghost = rect.inflate(-max(4, rect.width // 4), -max(4, rect.height // 4))
        pygame.draw.rect(
            surface,
            self._shade(PIECE_COLORS[kind], 0.72),
            ghost,
            width=max(1, rect.width // 13),
            border_radius=max(2, rect.width // 8),
        )

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        action: Command | str,
        active: bool,
        muted: bool,
    ) -> None:
        pygame.draw.rect(surface, BUTTON_ACTIVE if active else BUTTON, rect, border_radius=6)
        pygame.draw.rect(surface, (77, 84, 74), rect, width=1, border_radius=6)
        color = LIME if active else TEXT
        center = rect.center
        unit = max(4, rect.width // 7)

        if action in (Command.MOVE_LEFT, Command.MOVE_RIGHT, Command.SOFT_DROP):
            direction = {
                Command.MOVE_LEFT: (-1, 0),
                Command.MOVE_RIGHT: (1, 0),
                Command.SOFT_DROP: (0, 1),
            }[action]
            self._draw_arrow(surface, center, direction, unit, color)
        elif action is Command.HARD_DROP:
            self._draw_arrow(surface, (center[0], center[1] - unit // 2), (0, 1), unit, color)
            pygame.draw.line(
                surface,
                color,
                (center[0] - unit, center[1] + unit + 2),
                (center[0] + unit, center[1] + unit + 2),
                2,
            )
        elif action in (Command.ROTATE_CLOCKWISE, Command.ROTATE_COUNTERCLOCKWISE):
            clockwise = action is Command.ROTATE_CLOCKWISE
            self._draw_rotate(surface, rect, clockwise, color)
        elif action is Command.RESTART:
            self._draw_rotate(surface, rect, True, color)
            marker = max(4, rect.width // 9)
            pygame.draw.rect(
                surface,
                CORAL,
                (rect.centerx - marker // 2, rect.centery - marker // 2, marker, marker),
                border_radius=1,
            )
        elif action is Command.HOLD:
            self._draw_exchange(surface, rect, color)
        elif action is Command.TOGGLE_PAUSE:
            bar_width = max(3, rect.width // 9)
            bar_height = rect.height // 3
            pygame.draw.rect(
                surface,
                color,
                (center[0] - bar_width * 2, center[1] - bar_height // 2, bar_width, bar_height),
                border_radius=1,
            )
            pygame.draw.rect(
                surface,
                color,
                (center[0] + bar_width, center[1] - bar_height // 2, bar_width, bar_height),
                border_radius=1,
            )
        elif action == "mute":
            self._draw_speaker(surface, rect, color, muted)

    def _draw_arrow(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        direction: tuple[int, int],
        unit: int,
        color: Color,
    ) -> None:
        x, y = center
        dx, dy = direction
        start = (x - dx * unit, y - dy * unit)
        end = (x + dx * unit, y + dy * unit)
        pygame.draw.line(surface, color, start, end, max(2, unit // 3))
        perpendicular = (-dy, dx)
        points = [
            (x + dx * unit * 2, y + dy * unit * 2),
            (
                x + dx * unit // 2 + perpendicular[0] * unit,
                y + dy * unit // 2 + perpendicular[1] * unit,
            ),
            (
                x + dx * unit // 2 - perpendicular[0] * unit,
                y + dy * unit // 2 - perpendicular[1] * unit,
            ),
        ]
        pygame.draw.polygon(surface, color, points)

    def _draw_rotate(
        self, surface: pygame.Surface, rect: pygame.Rect, clockwise: bool, color: Color
    ) -> None:
        arc = rect.inflate(-rect.width // 3, -rect.height // 3)
        start, end = (0.15 * pi, 1.65 * pi) if clockwise else (-0.65 * pi, 0.85 * pi)
        pygame.draw.arc(surface, color, arc, start, end, max(2, rect.width // 16))
        x = arc.right - 1 if clockwise else arc.left + 1
        y = arc.centery - rect.height // 8
        direction = 1 if clockwise else -1
        pygame.draw.polygon(
            surface,
            color,
            [(x, y), (x - direction * 7, y - 4), (x - direction * 6, y + 5)],
        )

    def _draw_exchange(self, surface: pygame.Surface, rect: pygame.Rect, color: Color) -> None:
        left, right = rect.left + rect.width // 4, rect.right - rect.width // 4
        top, bottom = rect.top + rect.height // 3, rect.bottom - rect.height // 3
        pygame.draw.line(surface, color, (left, top), (right, top), 2)
        pygame.draw.line(surface, color, (right, bottom), (left, bottom), 2)
        pygame.draw.polygon(
            surface,
            color,
            [(right, top), (right - 7, top - 4), (right - 7, top + 4)],
        )
        pygame.draw.polygon(
            surface,
            color,
            [(left, bottom), (left + 7, bottom - 4), (left + 7, bottom + 4)],
        )

    def _draw_speaker(
        self, surface: pygame.Surface, rect: pygame.Rect, color: Color, muted: bool
    ) -> None:
        center_x, center_y = rect.center
        size = max(5, rect.width // 7)
        pygame.draw.polygon(
            surface,
            color,
            [
                (center_x - size * 2, center_y - size // 2),
                (center_x - size, center_y - size // 2),
                (center_x, center_y - size * 3 // 2),
                (center_x, center_y + size * 3 // 2),
                (center_x - size, center_y + size // 2),
                (center_x - size * 2, center_y + size // 2),
            ],
        )
        if muted:
            pygame.draw.line(
                surface,
                CORAL,
                (center_x + 2, center_y - size),
                (center_x + size * 2, center_y + size),
                3,
            )
        else:
            pygame.draw.arc(
                surface,
                color,
                (center_x - size // 2, center_y - size * 2, size * 3, size * 4),
                -0.7,
                0.7,
                2,
            )

    def _draw_status_overlay(
        self, surface: pygame.Surface, layout: Layout, state: GameState
    ) -> None:
        if state.status is GameStatus.PLAYING:
            return

        overlay = pygame.Surface(layout.board.size, pygame.SRCALPHA)
        overlay.fill((7, 9, 8, 222))
        surface.blit(overlay, layout.board.topleft)
        title = "PAUSED" if state.status is GameStatus.PAUSED else "RUN ENDED"
        accent = LIME if state.status is GameStatus.PAUSED else CORAL
        self._text(surface, title, 30, accent, layout.board.center, "center")
        if state.status is GameStatus.GAME_OVER:
            self._text(
                surface,
                f"{state.score:07d}",
                18,
                TEXT,
                (layout.board.centerx, layout.board.centery + 40),
                "center",
            )

    def _cell_rect(self, layout: Layout, x: int, board_y: int) -> pygame.Rect:
        return pygame.Rect(
            layout.board.left + x * layout.cell_size,
            layout.board.top + (board_y - HIDDEN_ROWS) * layout.cell_size,
            layout.cell_size,
            layout.cell_size,
        )

    def _text(
        self,
        surface: pygame.Surface,
        value: str,
        size: int,
        color: Color,
        position: tuple[int, int],
        anchor: str,
    ) -> None:
        rendered = self._font(size).render(value, True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, position)
        surface.blit(rendered, rect)

    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    @staticmethod
    def _shade(color: Color, factor: float) -> Color:
        return tuple(min(255, max(0, round(channel * factor))) for channel in color)  # type: ignore[return-value]
