import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PANEL_WIDTH,
    TILE_SIZE,
    COLORS,
    FPS,
)
from src.agent import Agent
from src.world import World


class PygameRenderer:
    def __init__(self, world: World):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 14)
        self.big_font = pygame.font.SysFont("consolas", 18, bold=True)

        self.selected_agent: Agent | None = None
        self.selected_tile: tuple[int, int] | None = None
        self.panel_padding = 14
        self.panel_gap = 8

    def select_tile_at_pixel(self, mouse_x: int, mouse_y: int):
        tile_x = mouse_x // TILE_SIZE
        tile_y = mouse_y // TILE_SIZE
        self.select_tile(tile_x, tile_y)

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
        self.screen.fill((0, 0, 0))

        self.draw_world()
        self.draw_panel(paused, sim_speed)

        pygame.display.flip()

    def draw_world(self):
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.tile_at(x, y)

                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                pygame.draw.rect(self.screen, COLORS[tile.kind], rect)
                pygame.draw.rect(self.screen, COLORS["grid"], rect, 1)

                if tile.food > 0:
                    self.draw_centered_symbol("f", x, y, COLORS["food"])

                if tile.wood > 0:
                    self.draw_centered_symbol("w", x, y, COLORS["wood"])

                agent = self.world.agent_at(x, y)
                if agent:
                    self.draw_centered_symbol("@", x, y, COLORS["agent"])

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

        rect = pygame.Rect(
            x * TILE_SIZE,
            y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.screen, color, rect, 3)

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
        panel_x = self.world.width * TILE_SIZE
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
        y = self.draw_stat_row("Tick", self.world.tick, content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Speed", f"{sim_speed}/s", content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Controls", content_x, y, content_width, bottom_y)
        controls = "Space pause | Up/Down speed | R restart | Esc quit"
        y = self.draw_wrapped_text(controls, content_x, y, content_width, bottom_y, COLORS["muted"])

        y += self.panel_gap
        y = self.draw_section_header("Colony", content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Living", len(self.world.living_agents()), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Shelters", self.world.count_tiles("shelter"), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Food", self.world.total_food_on_map(), content_x, y, content_width, bottom_y)
        y = self.draw_stat_row("Wood", self.world.total_wood_on_map(), content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_selection_details(content_x, y, content_width, bottom_y)

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
