import random
from dataclasses import dataclass, field

from src.building_priorities import highest_priority, needed_shelters
from src.colony_memory import ColonyMemory
from src.colony_storage import ColonyStorage
from src.environment_events import update_environment_events
from src.seasons import (
    day_of_season,
    next_season_index,
    season_for_index,
    should_advance_season,
    transition_progress,
)
from src.resource_ecology import apply_resource_ecology
from src.wildlife import spawn_wildlife, update_wildlife
from src.worldgen import generate_world
from src.agent import Agent


@dataclass
class World:
    width: int
    height: int

    tiles: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    events: list = field(default_factory=list)
    colony_memory: ColonyMemory = field(default_factory=ColonyMemory)
    colony_storage: ColonyStorage = field(default_factory=ColonyStorage)
    seed: int | None = None
    elevation_map: list[list[float]] = field(default_factory=list, repr=False)
    moisture_map: list[list[float]] = field(default_factory=list, repr=False)
    temperature_map: list[list[float]] = field(default_factory=list, repr=False)
    river_paths: list[list[tuple[int, int]]] = field(default_factory=list, repr=False)
    active_environment_events: list = field(default_factory=list)
    animals: list = field(default_factory=list)

    day: int = 1
    tick: int = 0
    season_index: int = 0

    @property
    def season(self) -> str:
        return season_for_index(self.season_index)

    @property
    def day_of_season(self) -> int:
        return day_of_season(self.day)

    @property
    def next_season(self) -> str:
        return season_for_index(next_season_index(self.season_index))

    @property
    def ticks_into_day(self) -> int:
        from src.config import TICKS_PER_DAY
        return self.tick % TICKS_PER_DAY

    @property
    def transition_progress(self) -> float:
        from src.config import TICKS_PER_DAY
        return transition_progress(self.day_of_season, self.ticks_into_day, TICKS_PER_DAY)

    @property
    def season_label(self) -> str:
        if self.transition_progress > 0.0:
            return f"{self.season} -> {self.next_season}"
        return self.season

    def generate(self, seed: int | None = None):
        if seed is not None:
            self.seed = seed

        (
            self.tiles,
            self.elevation_map,
            self.moisture_map,
            self.temperature_map,
            self.river_paths,
        ) = generate_world(self.width, self.height, self.seed)
        self.animals = spawn_wildlife(self, random.Random(self.seed))

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

        from src.config import TICKS_PER_DAY
        if self.tick % TICKS_PER_DAY == 0:
            self.advance_day()

        for agent in self.living_agents():
            agent.update_needs()
            agent.scan_surroundings(self)
            action = agent.choose_action(self)
            action.execute(agent, self)
            agent.die_if_needed(self)

        update_wildlife(self, random)

    def advance_day(self):
        self.day += 1
        if should_advance_season(self.day):
            self.advance_season()

        update_environment_events(self, random)
        self.regrow_resources()
        self.log(f"Day {self.day} begins.")

    def advance_season(self):
        self.season_index = next_season_index(self.season_index)
        self.log(f"{self.season} begins.")

    def regrow_resources(self):
        for row in self.tiles:
            for tile in row:
                apply_resource_ecology(tile, self.season, random, self.active_environment_events)

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

    def animal_at(self, x, y):
        for animal in self.animals:
            if animal.alive and animal.x == x and animal.y == y:
                return animal

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
        return needed_shelters(self)

    def needs_more_shelters(self):
        return self.building_priority() is not None

    def building_priority(self):
        return highest_priority(self)

    def highest_building_priority(self):
        priority = self.building_priority()
        if priority is None:
            return None
        return priority.building_type

    def should_gather_wood_for_construction(self, agent):
        from src.building_priorities import should_gather_wood_for_construction
        return should_gather_wood_for_construction(agent, self)

    def should_build_shelter(self, agent):
        from src.building_priorities import should_build_shelter
        return should_build_shelter(agent, self)

    def total_food_on_map(self):
        return sum(tile.food for row in self.tiles for tile in row)

    def total_wood_on_map(self):
        return sum(tile.wood for row in self.tiles for tile in row)

    def log(self, message):
        self.events.append(f"Day {self.day}: {message}")

        if len(self.events) > 100:
            self.events = self.events[-100:]


def create_world(
    width: int | None = None,
    height: int | None = None,
    agent_count: int | None = None,
    seed: int | None = None,
):
    from src.config import WIDTH, HEIGHT, STARTING_AGENTS, WORLD_SEED

    world = World(
        width if width is not None else WIDTH,
        height if height is not None else HEIGHT,
        seed=seed if seed is not None else WORLD_SEED,
    )
    world.generate()
    world.spawn_agents(agent_count if agent_count is not None else STARTING_AGENTS)
    return world
