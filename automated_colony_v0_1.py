import random
from dataclasses import dataclass, field

import pygame


WIDTH = 50
HEIGHT = 28
TILE_SIZE = 22
PANEL_WIDTH = 360
STARTING_AGENTS = 10

SCREEN_WIDTH = WIDTH * TILE_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = HEIGHT * TILE_SIZE

FPS = 30
SIM_TICKS_PER_SECOND = 8


COLORS = {
    "grass": (75, 145, 75),
    "forest": (25, 95, 35),
    "water": (45, 95, 170),
    "mountain": (110, 110, 110),
    "shelter": (145, 95, 45),
    "food": (230, 80, 80),
    "wood": (130, 80, 35),
    "agent": (245, 245, 245),
    "dead": (90, 90, 90),
    "grid": (20, 20, 20),
    "panel": (24, 24, 28),
    "text": (230, 230, 230),
    "muted": (160, 160, 160),
    "warning": (240, 180, 80),
}


@dataclass
class Tile:
    kind: str
    food: int = 0
    wood: int = 0

    @property
    def walkable(self):
        return self.kind not in ("water", "mountain")


@dataclass
class Agent:
    name: str
    x: int
    y: int

    hunger: int = 0
    thirst: int = 0
    fatigue: int = 0

    food: int = 0
    wood: int = 0

    alive: bool = True
    current_action: str = "Idle"

    def update_needs(self):
        self.hunger += 1
        self.thirst += 2
        self.fatigue += 1

    def choose_action(self, world):
        actions = [
            EatAction(),
            DrinkAction(),
            GatherFoodAction(),
            GatherWoodAction(),
            BuildShelterAction(),
            SleepAction(),
            WanderAction(),
        ]

        valid_actions = [action for action in actions if action.can_do(self, world)]
        return max(valid_actions, key=lambda action: action.score(self, world))

    def die_if_needed(self, world):
        if self.hunger >= 100:
            self.alive = False
            self.current_action = "Dead"
            world.log(f"{self.name} died of starvation.")
        elif self.thirst >= 100:
            self.alive = False
            self.current_action = "Dead"
            world.log(f"{self.name} died of thirst.")


class Action:
    name = "Action"

    def can_do(self, agent, world):
        return True

    def score(self, agent, world):
        return 0

    def execute(self, agent, world):
        agent.current_action = self.name


class EatAction(Action):
    name = "Eating"

    def can_do(self, agent, world):
        return agent.food > 0 and agent.hunger > 20

    def score(self, agent, world):
        return agent.hunger * 3

    def execute(self, agent, world):
        super().execute(agent, world)
        agent.food -= 1
        agent.hunger = max(0, agent.hunger - 60)
        world.log(f"{agent.name} eats stored food.")


class DrinkAction(Action):
    name = "Drinking"

    def can_do(self, agent, world):
        return world.nearby_tile_kind(agent.x, agent.y, "water") and agent.thirst > 10

    def score(self, agent, world):
        return agent.thirst * 4

    def execute(self, agent, world):
        super().execute(agent, world)
        agent.thirst = 0
        world.log(f"{agent.name} drinks water.")


class GatherFoodAction(Action):
    name = "Gathering food"

    def can_do(self, agent, world):
        return world.tile_at(agent.x, agent.y).food > 0

    def score(self, agent, world):
        return 45 + agent.hunger

    def execute(self, agent, world):
        super().execute(agent, world)
        tile = world.tile_at(agent.x, agent.y)
        tile.food -= 1
        agent.food += 1
        world.log(f"{agent.name} gathers food.")


class GatherWoodAction(Action):
    name = "Gathering wood"

    def can_do(self, agent, world):
        return world.tile_at(agent.x, agent.y).wood > 0

    def score(self, agent, world):
        if agent.wood < 3:
            return 35
        return 8

    def execute(self, agent, world):
        super().execute(agent, world)
        tile = world.tile_at(agent.x, agent.y)
        tile.wood -= 1
        agent.wood += 1
        world.log(f"{agent.name} gathers wood.")


class BuildShelterAction(Action):
    name = "Building shelter"

    def can_do(self, agent, world):
        tile = world.tile_at(agent.x, agent.y)
        return agent.wood >= 3 and tile.kind == "grass"

    def score(self, agent, world):
        if world.count_tiles("shelter") < 3:
            return 80
        return 12

    def execute(self, agent, world):
        super().execute(agent, world)
        tile = world.tile_at(agent.x, agent.y)
        tile.kind = "shelter"
        agent.wood -= 3
        world.log(f"{agent.name} builds a shelter.")


class SleepAction(Action):
    name = "Sleeping"

    def can_do(self, agent, world):
        return agent.fatigue > 40 and world.tile_at(agent.x, agent.y).kind == "shelter"

    def score(self, agent, world):
        return agent.fatigue * 2

    def execute(self, agent, world):
        super().execute(agent, world)
        agent.fatigue = 0
        world.log(f"{agent.name} sleeps in a shelter.")


class WanderAction(Action):
    name = "Wandering"

    def score(self, agent, world):
        return random.randint(1, 10)

    def execute(self, agent, world):
        super().execute(agent, world)

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx = agent.x + dx
            ny = agent.y + dy

            if world.can_move_to(nx, ny):
                agent.x = nx
                agent.y = ny
                return


@dataclass
class World:
    width: int
    height: int

    tiles: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    events: list = field(default_factory=list)

    day: int = 1
    tick: int = 0

    def generate(self):
        self.tiles = []

        for y in range(self.height):
            row = []

            for x in range(self.width):
                roll = random.random()

                if roll < 0.07:
                    kind = "water"
                elif roll < 0.14:
                    kind = "mountain"
                elif roll < 0.35:
                    kind = "forest"
                else:
                    kind = "grass"

                tile = Tile(kind)

                if kind == "grass" and random.random() < 0.08:
                    tile.food = random.randint(1, 3)

                if kind == "forest":
                    tile.wood = random.randint(1, 4)

                    if random.random() < 0.18:
                        tile.food = random.randint(1, 2)

                row.append(tile)

            self.tiles.append(row)

    def spawn_agents(self, amount):
        names = [
            "Ari", "Bryn", "Cato", "Dara", "Eli",
            "Fenn", "Gala", "Hale", "Ira", "Juno",
        ]

        for i in range(amount):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

                if self.can_move_to(x, y):
                    self.agents.append(Agent(names[i % len(names)], x, y))
                    break

        self.log(f"{amount} villagers enter the world.")

    def update(self):
        self.tick += 1

        if self.tick % 50 == 0:
            self.day += 1
            self.regrow_resources()
            self.log(f"Day {self.day} begins.")

        for agent in self.living_agents():
            agent.update_needs()
            action = agent.choose_action(self)
            action.execute(agent, self)
            agent.die_if_needed(self)

    def regrow_resources(self):
        for row in self.tiles:
            for tile in row:
                if tile.kind == "grass" and random.random() < 0.03:
                    tile.food += 1

                if tile.kind == "forest":
                    if random.random() < 0.08:
                        tile.wood += 1

                    if random.random() < 0.04:
                        tile.food += 1

    def living_agents(self):
        return [agent for agent in self.agents if agent.alive]

    def tile_at(self, x, y):
        return self.tiles[y][x]

    def can_move_to(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        if not self.tile_at(x, y).walkable:
            return False

        return self.agent_at(x, y) is None

    def agent_at(self, x, y):
        for agent in self.living_agents():
            if agent.x == x and agent.y == y:
                return agent

        return None

    def nearby_tile_kind(self, x, y, kind):
        for dx, dy in [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx = x + dx
            ny = y + dy

            if 0 <= nx < self.width and 0 <= ny < self.height:
                if self.tile_at(nx, ny).kind == kind:
                    return True

        return False

    def count_tiles(self, kind):
        return sum(
            1
            for row in self.tiles
            for tile in row
            if tile.kind == kind
        )

    def total_food_on_map(self):
        return sum(tile.food for row in self.tiles for tile in row)

    def total_wood_on_map(self):
        return sum(tile.wood for row in self.tiles for tile in row)

    def log(self, message):
        self.events.append(f"Day {self.day}: {message}")

        if len(self.events) > 100:
            self.events = self.events[-100:]


class PygameRenderer:
    def __init__(self, world):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 16)
        self.big_font = pygame.font.SysFont("consolas", 22, bold=True)

    def draw(self, paused, sim_speed):
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

    def draw_centered_symbol(self, symbol, x, y, color):
        surface = self.font.render(symbol, True, color)
        rect = surface.get_rect(
            center=(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
        )
        self.screen.blit(surface, rect)

    def draw_panel(self, paused, sim_speed):
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

    def draw_line(self, text, x, y, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 4

    def limit_fps(self):
        self.clock.tick(FPS)


def create_world():
    world = World(WIDTH, HEIGHT)
    world.generate()
    world.spawn_agents(STARTING_AGENTS)
    return world


def main():
    world = create_world()
    renderer = PygameRenderer(world)

    running = True
    paused = False
    sim_speed = SIM_TICKS_PER_SECOND

    accumulator = 0

    while running:
        dt = renderer.clock.get_time() / 1000
        accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_UP:
                    sim_speed = min(60, sim_speed + 1)

                elif event.key == pygame.K_DOWN:
                    sim_speed = max(1, sim_speed - 1)

                elif event.key == pygame.K_r:
                    world = create_world()
                    renderer.world = world
                    accumulator = 0

        if not paused and len(world.living_agents()) > 0:
            step_time = 1 / sim_speed

            while accumulator >= step_time:
                world.update()
                accumulator -= step_time

        renderer.draw(paused, sim_speed)
        renderer.limit_fps()

    pygame.quit()


if __name__ == "__main__":
    main()