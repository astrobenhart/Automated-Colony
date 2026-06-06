import random
import math
from dataclasses import dataclass, field

from src.colony_memory import ColonyMemory
from src.config import SHELTER_CAPACITY
from src.tile import Tile
from src.agent import Agent


@dataclass
class World:
    width: int
    height: int

    tiles: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    events: list = field(default_factory=list)
    colony_memory: ColonyMemory = field(default_factory=ColonyMemory)

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
            agent.scan_surroundings(self)
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

    def needed_shelters(self):
        living_count = len(self.living_agents())
        if living_count == 0:
            return 0
        return math.ceil(living_count / SHELTER_CAPACITY)

    def needs_more_shelters(self):
        return self.count_tiles("shelter") < self.needed_shelters()

    def total_food_on_map(self):
        return sum(tile.food for row in self.tiles for tile in row)

    def total_wood_on_map(self):
        return sum(tile.wood for row in self.tiles for tile in row)

    def log(self, message):
        self.events.append(f"Day {self.day}: {message}")

        if len(self.events) > 100:
            self.events = self.events[-100:]


def create_world():
    from src.config import WIDTH, HEIGHT, STARTING_AGENTS
    world = World(WIDTH, HEIGHT)
    world.generate()
    world.spawn_agents(STARTING_AGENTS)
    return world
