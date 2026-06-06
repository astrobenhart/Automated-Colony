import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PANEL_WIDTH,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    TILE_SIZE,
    CAMERA_STEP,
    DEBUG_DRAW_GRID,
    COLORS,
    TERRAIN_LABELS,
    SYMBOL_LABELS,
    FPS,
)
from src.environment_events import active_event_names, environmental_tile_color
from src.resource_ecology import max_food, max_wood
from src.seasons import seasonal_tile_color
from src.agent import Agent
from src.world import World


class PygameRenderer:
    def __init__(self, world: World):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 13)
        self.big_font = pygame.font.SysFont("consolas", 17, bold=True)

        self.selected_agent: Agent | None = None
        self.selected_tile: tuple[int, int] | None = None
        self.panel_padding = 14
        self.panel_gap = 8
        self.camera_x = 0
        self.camera_y = 0

    def set_world(self, world: World):
        self.world = world
        self.clear_selection()
        self.clamp_camera()

    def select_tile_at_pixel(self, mouse_x: int, mouse_y: int):
        tile = self.screen_to_world_tile(mouse_x, mouse_y)
        if tile is None:
            self.clear_selection()
            return

        tile_x, tile_y = tile
        self.select_tile(tile_x, tile_y)

    def screen_to_world_tile(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        map_width = VIEWPORT_WIDTH * TILE_SIZE
        map_height = VIEWPORT_HEIGHT * TILE_SIZE
        if not (0 <= mouse_x < map_width and 0 <= mouse_y < map_height):
            return None

        return (
            self.camera_x + mouse_x // TILE_SIZE,
            self.camera_y + mouse_y // TILE_SIZE,
        )

    def camera_step(self) -> int:
        return CAMERA_STEP

    def pan_camera(self, dx: int, dy: int):
        self.camera_x += dx
        self.camera_y += dy
        self.clamp_camera()

    def clamp_camera(self):
        max_x = max(0, self.world.width - VIEWPORT_WIDTH)
        max_y = max(0, self.world.height - VIEWPORT_HEIGHT)
        self.camera_x = max(0, min(self.camera_x, max_x))
        self.camera_y = max(0, min(self.camera_y, max_y))

    def visible_tile_bounds(self) -> tuple[int, int, int, int]:
        self.clamp_camera()
        start_x = self.camera_x
        start_y = self.camera_y
        end_x = min(self.world.width, start_x + VIEWPORT_WIDTH)
        end_y = min(self.world.height, start_y + VIEWPORT_HEIGHT)
        return start_x, start_y, end_x, end_y

    def select_tile(self, tile_x: int, tile_y: int):
        if not (0 <= tile_x < self.world.width and 0 <= tile_y < self.world.height):
            self.clear_selection()
            return

        agent = self.world.agent_at(tile_x, tile_y)
        if agent is not None:
            self.selected_agent = agent
            self.selected_tile = None
            return

        self.selected_agent = None
        self.selected_tile = (tile_x, tile_y)

    def clear_selection(self):
        self.selected_agent = None
        self.selected_tile = None

    def validate_selection(self):
        if self.selected_agent is not None and self.selected_agent not in self.world.agents:
            self.clear_selection()

        if self.selected_tile is not None:
            x, y = self.selected_tile
            if not (0 <= x < self.world.width and 0 <= y < self.world.height):
                self.clear_selection()

    def draw(self, paused: bool, sim_speed: int):
        self.validate_selection()
        self.clamp_camera()
        self.screen.fill((0, 0, 0))

        self.draw_world()
        self.draw_panel(paused, sim_speed)

        pygame.display.flip()

    def draw_world(self):
        start_x, start_y, end_x, end_y = self.visible_tile_bounds()

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.world.tile_at(x, y)
                screen_x = x - start_x
                screen_y = y - start_y

                rect = pygame.Rect(
                    screen_x * TILE_SIZE,
                    screen_y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                pygame.draw.rect(self.screen, self.tile_color(tile.kind), rect)
                if DEBUG_DRAW_GRID:
                    pygame.draw.rect(self.screen, COLORS["grid"], rect, 1)

                if tile.food > 0:
                    self.draw_centered_symbol("f", screen_x, screen_y, self.resource_color("food", tile.food, max_food(tile)))

                if tile.wood > 0:
                    self.draw_centered_symbol("w", screen_x, screen_y, self.resource_color("wood", tile.wood, max_wood(tile)))

                agent = self.world.agent_at(x, y)
                if agent:
                    self.draw_centered_symbol("@", screen_x, screen_y, COLORS["agent"])

        self.draw_selection_highlight()

    def draw_selection_highlight(self):
        if self.selected_agent is not None:
            x = self.selected_agent.x
            y = self.selected_agent.y
            color = COLORS["selection_agent"]
        elif self.selected_tile is not None:
            x, y = self.selected_tile
            color = COLORS["selection"]
        else:
            return

        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        if not (start_x <= x < end_x and start_y <= y < end_y):
            return

        screen_x = x - start_x
        screen_y = y - start_y

        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.screen, color, rect, 2)

    def draw_centered_symbol(self, symbol: str, x: int, y: int, color: tuple):
        surface = self.font.render(symbol, True, color)
        rect = surface.get_rect(
            center=(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
        )
        self.screen.blit(surface, rect)

    def draw_panel(self, paused: bool, sim_speed: int):
        panel_x = VIEWPORT_WIDTH * TILE_SIZE
        content_x = panel_x + self.panel_padding
        content_width = PANEL_WIDTH - self.panel_padding * 2
        bottom_y = SCREEN_HEIGHT - self.panel_padding

        pygame.draw.rect(
            self.screen,
            COLORS["panel"],
            pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT),
        )

        y = self.panel_padding

        y = self.draw_text_line(
            "Automated Colony",
            content_x,
            y,
            content_width,
            bottom_y,
            self.big_font,
        )
        y += self.panel_gap

        y = self.draw_section_header("Simulation", content_x, y, content_width, bottom_y)
        status = "PAUSED" if paused else "RUNNING"
        y = self.draw_stat_row("State", status, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Day", self.world.day, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Season", self.world.season_label, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("S Day", self.world.day_of_season, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Tick", self.world.tick, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Speed", f"{sim_speed}/s", content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Camera", f"({self.camera_x}, {self.camera_y})", content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Events", active_event_names(self.world.active_environment_events), content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Controls", content_x, y, content_width, bottom_y)
        controls = "WASD pan | Space pause | Up/Down speed | R restart | Esc quit"
        y = self.draw_wrapped_text(controls, content_x, y, content_width, bottom_y, COLORS["muted"])

        y += self.panel_gap
        y = self.draw_section_header("Colony", content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Living", len(self.world.living_agents()), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Shelters", self.world.count_tiles("shelter"), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Food", self.world.total_food_on_map(), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Wood", self.world.total_wood_on_map(), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Stored F", self.world.colony_storage.food, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Stored W", self.world.colony_storage.wood, content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_selection_details(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_legend(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Recent Events", content_x, y, content_width, bottom_y)
        line_height = self.font.get_height() + 3
        max_events = max(0, (bottom_y - y) // line_height)
        if max_events > 0:
            for event in self.world.events[-max_events:]:
                y = self.draw_text_line(event, content_x, y, content_width, bottom_y, color=COLORS["muted"])

    def draw_selection_details(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Selection", x, y, width, bottom_y)

        if self.selected_agent is not None:
            agent = self.selected_agent
            target = agent.current_target if agent.current_target is not None else "None"
            details = [
                ("Agent", agent.name),
                ("Pos", f"({agent.x}, {agent.y})"),
                ("Needs", f"H{agent.hunger} T{agent.thirst} F{agent.fatigue}"),
                ("Carry", f"Food {agent.food}, Wood {agent.wood}"),
                ("Action", agent.current_action),
                ("Goal", agent.current_goal),
                ("Target", target),
            ]
            color = COLORS["text"] if agent.alive else COLORS["dead"]

        elif self.selected_tile is not None:
            tile_x, tile_y = self.selected_tile
            tile = self.world.tile_at(tile_x, tile_y)
            details = [
                ("Tile", f"({tile_x}, {tile_y})"),
                ("Terrain", tile.kind),
                ("Food", tile.food),
                ("Wood", tile.wood),
                ("Walkable", tile.walkable),
            ]
            color = COLORS["text"]

        else:
            details = [("Selected", "None")]
            color = COLORS["muted"]

        for label, value in details:
            y = self.draw_stat_row(label, value, x, y, width, bottom_y, color=color)

        return y

    def draw_legend(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header(f"Legend ({self.world.season_label})", x, y, width, bottom_y)
        column_width = width // 2
        row_height = self.font.get_height() + 3
        items = list(TERRAIN_LABELS.items())

        for index in range(0, len(items), 2):
            if y + row_height > bottom_y:
                return y

            for column, (kind, label) in enumerate(items[index:index + 2]):
                item_x = x + column * column_width
                self.draw_legend_item(kind, label, item_x, y, column_width - 8)

            y += row_height

        symbol_text = "  ".join(f"{symbol} {label}" for symbol, label in SYMBOL_LABELS.items())
        y = self.draw_text_line(symbol_text, x, y, width, bottom_y, color=COLORS["muted"])
        return y

    def draw_legend_item(self, kind: str, label: str, x: int, y: int, width: int):
        swatch_size = 10
        swatch_y = y + max(0, (self.font.get_height() - swatch_size) // 2)
        pygame.draw.rect(
            self.screen,
            self.tile_color(kind),
            pygame.Rect(x, swatch_y, swatch_size, swatch_size),
        )

        text_x = x + swatch_size + 6
        text_width = max(0, width - swatch_size - 6)
        surface = self.font.render(self.fit_text(label, self.font, text_width), True, COLORS["text"])
        self.screen.blit(surface, (text_x, y))

    def tile_color(self, kind: str):
        season_color = seasonal_tile_color(
            kind,
            self.world.season,
            self.world.next_season,
            self.world.transition_progress,
        )
        return environmental_tile_color(season_color, kind, self.world.active_environment_events)

    def resource_color(self, resource: str, amount: int, cap: int):
        base = COLORS[resource]
        if cap <= 1:
            strength = 1.0
        else:
            strength = max(0.35, min(1.0, amount / cap))

        muted = tuple(max(40, round(channel * 0.45)) for channel in base)
        return tuple(
            round(muted_channel + (base_channel - muted_channel) * strength)
            for muted_channel, base_channel in zip(muted, base)
        )

    def draw_section_header(self, text: str, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_text_line(text, x, y, width, bottom_y, self.big_font)
        return y + 2

    def draw_stat_row(
        self,
        label: str,
        value,
        x: int,
        y: int,
        width: int,
        bottom_y: int,
        color=None,
    ):
        label_text = f"{label}:"
        value_text = str(value)
        line = f"{label_text:<10} {value_text}"
        return self.draw_text_line(line, x, y, width, bottom_y, color=color)

    def draw_wrapped_text(self, text: str, x: int, y: int, width: int, bottom_y: int, color=None):
        words = text.split()
        line = ""

        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.font.size(candidate)[0] <= width:
                line = candidate
                continue

            if line:
                y = self.draw_text_line(line, x, y, width, bottom_y, color=color)
            line = word

        if line:
            y = self.draw_text_line(line, x, y, width, bottom_y, color=color)

        return y

    def draw_text_line(self, text: str, x: int, y: int, width: int, bottom_y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        if y + font.get_height() > bottom_y:
            return y

        surface = font.render(self.fit_text(str(text), font, width), True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 3

    def fit_text(self, text: str, font, max_width: int):
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        available_width = max_width - font.size(ellipsis)[0]
        if available_width <= 0:
            return ellipsis

        fitted = ""
        for char in text:
            if font.size(fitted + char)[0] > available_width:
                break
            fitted += char

        return fitted + ellipsis

    def draw_line(self, text: str, x: int, y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 4

    def limit_fps(self):
        self.clock.tick(FPS)
