import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PANEL_WIDTH,
    TILE_SIZE,
    COLORS,
    FPS,
)
from src.world import World


class PygameRenderer:
    def __init__(self, world: World):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 22, bold=True)

    def draw(self, paused: bool, sim_speed: int):
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

        pygame.draw.rect(
            self.screen,
            COLORS["panel"],
            pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT),
        )

        y = 14

        y = self.draw_line("Automated Colony", panel_x + 16, y, self.big_font)
        y += 8

        status = "PAUSED" if paused else "RUNNING"
        y = self.draw_line(f"Status: {status}", panel_x + 16, y)
        y = self.draw_line(f"Speed: {sim_speed} ticks/sec", panel_x + 16, y)
        y = self.draw_line(f"Day: {self.world.day}", panel_x + 16, y)
        y = self.draw_line(f"Tick: {self.world.tick}", panel_x + 16, y)
        y = self.draw_line(f"Living villagers: {len(self.world.living_agents())}", panel_x + 16, y)
        y = self.draw_line(f"Shelters: {self.world.count_tiles('shelter')}", panel_x + 16, y)
        y = self.draw_line(f"Map food: {self.world.total_food_on_map()}", panel_x + 16, y)
        y = self.draw_line(f"Map wood: {self.world.total_wood_on_map()}", panel_x + 16, y)

        y += 12
        y = self.draw_line("Controls", panel_x + 16, y, self.big_font)
        y += 4

        controls = [
            "SPACE - pause/unpause",
            "UP    - faster",
            "DOWN  - slower",
            "R     - restart",
            "ESC   - quit",
        ]

        for line in controls:
            y = self.draw_line(line, panel_x + 16, y, color=COLORS["muted"])

        y += 12
        y = self.draw_line("Villagers", panel_x + 16, y, self.big_font)
        y += 4

        for agent in self.world.agents[:10]:
            if agent.alive:
                line = (
                    f"{agent.name}: H{agent.hunger:02} "
                    f"T{agent.thirst:02} F{agent.fatigue:02} "
                    f"{agent.current_action}"
                )
                color = COLORS["text"]

                if agent.hunger > 70 or agent.thirst > 70:
                    color = COLORS["warning"]
            else:
                line = f"{agent.name}: dead"
                color = COLORS["dead"]

            y = self.draw_line(line[:38], panel_x + 16, y, color=color)

        y += 12
        y = self.draw_line("Recent Events", panel_x + 16, y, self.big_font)
        y += 4

        for event in self.world.events[-12:]:
            y = self.draw_line(event[-40:], panel_x + 16, y, color=COLORS["muted"])

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
