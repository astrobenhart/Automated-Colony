import random
from dataclasses import dataclass, field

from src.building_priorities import highest_priority, needed_shelters, update_settlement_needs
from src.appearance import appearance_seed_for, appearance_type_for_seed
from src.carrying_capacity import carrying_capacity_report
from src.colony_memory import ColonyMemory
from src.colony_storage import ColonyStorage
from src.environment_events import update_environment_events
from src.farming import maybe_create_farm, update_farms
from src.influence import update_influence_peaks
from src.death_memory import DeathRecord, expire_remembrances
from src.seasons import (
    day_of_season,
    next_season_index,
    season_for_index,
    should_advance_season,
    transition_progress,
)
from src.resource_ecology import apply_resource_ecology
from src.lifecycle import lifecycle_stage_for_index
from src.roles import role_for_index
from src.social_memory import update_social_memory
from src.traits import trait_for_index
from src.settlement import (
    Settlement,
    choose_resource_target,
    distance_to_settlement,
    filter_positions_by_settlement_radius,
    found_settlement,
    is_within_resource_radius,
    resource_search_radius,
    update_resource_pressures,
)
from src.wildlife import spawn_wildlife, update_wildlife
from src.world_history import WorldHistory
from src.world_identity import WorldIdentity, generate_world_identity
from src.worldgen_settings import WorldGenSettings, default_worldgen_settings
from src.worldgen import generate_world
from src.agent import Agent
from src.profiler import profiler
from src.reservations import ReservationManager


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
    settings: WorldGenSettings = field(default_factory=default_worldgen_settings)
    elevation_map: list[list[float]] = field(default_factory=list, repr=False)
    moisture_map: list[list[float]] = field(default_factory=list, repr=False)
    temperature_map: list[list[float]] = field(default_factory=list, repr=False)
    river_paths: list[list[tuple[int, int]]] = field(default_factory=list, repr=False)
    active_environment_events: list = field(default_factory=list)
    animals: list = field(default_factory=list)
    history: WorldHistory = field(default_factory=WorldHistory)
    death_records: list[DeathRecord] = field(default_factory=list)
    identity: WorldIdentity | None = None
    settlement: Settlement | None = None
    reservations: ReservationManager = field(default_factory=ReservationManager)

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

    @property
    def year(self) -> int:
        from src.config import DAYS_PER_SEASON, SEASONS
        days_per_year = DAYS_PER_SEASON * len(SEASONS)
        return ((self.day - 1) // days_per_year) + 1

    def generate(self, seed: int | None = None):
        if seed is not None:
            self.seed = seed

        self.settings = self.settings.with_overrides(
            width=self.width,
            height=self.height,
            seed=self.seed,
        )
        (
            self.tiles,
            self.elevation_map,
            self.moisture_map,
            self.temperature_map,
            self.river_paths,
        ) = generate_world(self.width, self.height, self.seed, self.settings)
        self.animals = spawn_wildlife(self, random.Random(self.seed))
        self.identity = generate_world_identity(self)

    def spawn_agents(self, amount):
        if self.settlement is None:
            self.establish_settlement()

        names = [
            "Ari", "Bryn", "Cato", "Dara", "Eli",
            "Fenn", "Gala", "Hale", "Ira", "Juno",
        ]

        positions = self.initial_spawn_positions(amount)
        for i, (x, y) in enumerate(positions):
            appearance_seed = appearance_seed_for(self.seed, i, names[i % len(names)])
            self.agents.append(Agent(
                names[i % len(names)],
                x,
                y,
                role=role_for_index(i),
                lifecycle_stage=lifecycle_stage_for_index(i),
                trait=trait_for_index(i),
                agent_id=f"villager-{i}",
                appearance_seed=appearance_seed,
                appearance_type=appearance_type_for_seed(appearance_seed),
            ))

        self.update_settlement_population()
        self.log(f"{amount} villagers enter the world.")

    def establish_settlement(self):
        self.settlement = found_settlement(self)

    def initial_spawn_positions(self, amount):
        from src.config import INITIAL_SPAWN_MAX_RADIUS, INITIAL_SPAWN_RADIUS

        if amount <= 0:
            return []
        if self.settlement is None:
            return self._fallback_spawn_positions(amount)

        positions = []
        reserved = set()
        for radius in range(INITIAL_SPAWN_RADIUS, INITIAL_SPAWN_MAX_RADIUS + 1):
            for pos in self._spawn_candidates_in_radius(radius, reserved):
                positions.append(pos)
                reserved.add(pos)
                if len(positions) == amount:
                    return positions

        for pos in self._spawn_candidates_in_radius(max(self.width, self.height), reserved):
            positions.append(pos)
            reserved.add(pos)
            if len(positions) == amount:
                return positions

        return positions

    def _spawn_candidates_in_radius(self, radius, reserved):
        settlement = self.settlement
        if settlement is None:
            return []

        candidates = []
        for y in range(max(0, settlement.y - radius), min(self.height, settlement.y + radius + 1)):
            for x in range(max(0, settlement.x - radius), min(self.width, settlement.x + radius + 1)):
                distance = max(abs(x - settlement.x), abs(y - settlement.y))
                if distance > radius:
                    continue
                if not self.is_valid_spawn_tile(x, y, reserved):
                    continue
                candidates.append((distance, abs(x - settlement.x) + abs(y - settlement.y), y, x))

        return [(x, y) for _, _, y, x in sorted(candidates)]

    def _fallback_spawn_positions(self, amount):
        positions = []
        reserved = set()
        for y in range(self.height):
            for x in range(self.width):
                if not self.is_valid_spawn_tile(x, y, reserved):
                    continue
                positions.append((x, y))
                reserved.add((x, y))
                if len(positions) == amount:
                    return positions
        return positions

    def is_valid_spawn_tile(self, x, y, reserved=None):
        reserved = reserved or set()
        if (x, y) in reserved:
            return False
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        tile = self.tile_at(x, y)
        if not tile.walkable or tile.kind in ("water", "mountain"):
            return False
        if self.agent_at(x, y) is not None:
            return False
        if self.settlement is not None and (x, y) == (self.settlement.x, self.settlement.y):
            return False
        if self.stockpile_at(x, y) is not None:
            return False
        if self.workshop_at(x, y) is not None:
            return False
        return True

    def update_settlement_population(self):
        if self.settlement is not None:
            self.settlement.population = len(self.living_agents())

    def update_settlement_needs(self, force: bool = False):
        update_settlement_needs(self, force)

    def update_carrying_capacity(self):
        if self.settlement is not None:
            self.settlement.carrying_capacity_report = carrying_capacity_report(self)

    def record_settlement_activity(self):
        if self.settlement is None:
            return
        for agent in self.living_agents():
            self.settlement.record_activity(agent.x, agent.y)

    def update_resource_pressures(self):
        update_resource_pressures(self)

    def distance_to_settlement(self, x, y):
        return distance_to_settlement(self, x, y)

    def is_within_resource_radius(self, x, y, radius=None):
        return is_within_resource_radius(self, x, y, radius)

    def filter_positions_by_settlement_radius(self, positions, radius=None):
        return filter_positions_by_settlement_radius(self, positions, radius)

    def get_resource_search_radius(self, resource_type, agent=None):
        return resource_search_radius(self, resource_type, agent)

    def choose_resource_target(self, agent, resource_type, candidates):
        return choose_resource_target(self, agent, resource_type, candidates)

    def update(self):
        with profiler.time("world update"):
            self.tick += 1
            self.reservations.cleanup(self)

            from src.config import TICKS_PER_DAY
            if self.tick % TICKS_PER_DAY == 0:
                self.advance_day()

            for agent in self.living_agents():
                agent.update_needs()
                agent.scan_surroundings(self)
                progress_before = agent.progress_snapshot(self)
                action = agent.choose_action(self)
                action.execute(agent, self)
                agent.die_if_needed(self)
                if agent.alive:
                    agent.update_progress_tracking(self, progress_before)
                    if agent.current_action == "Recovering":
                        agent.release_reservations(self)

            self.update_settlement_population()
            self.update_settlement_needs(force=True)
            self.update_resource_pressures()
            self.update_carrying_capacity()
            self.record_settlement_activity()
            update_wildlife(self, random)

    def advance_day(self):
        self.day += 1
        if should_advance_season(self.day):
            self.advance_season()

        update_environment_events(self, random)
        self.regrow_resources()
        update_farms(self)
        self.update_resource_pressures()
        maybe_create_farm(self)
        self.update_carrying_capacity()
        update_social_memory(self)
        update_influence_peaks(self)
        expire_remembrances(self)
        self.log(f"Day {self.day} begins.")

    def advance_season(self):
        self.season_index = next_season_index(self.season_index)
        self.log(f"{self.season} begins.")

    def regrow_resources(self):
        for row in self.tiles:
            for tile in row:
                apply_resource_ecology(tile, self.season, random, self.active_environment_events, self.settings)

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

    def stockpile_at(self, x, y):
        if self.settlement is None:
            return None
        for stockpile in self.settlement.stockpiles:
            if stockpile.x == x and stockpile.y == y:
                return stockpile
        return None

    def workshop_at(self, x, y):
        if self.settlement is None:
            return None
        for workshop in self.settlement.workshops:
            if workshop.x == x and workshop.y == y:
                return workshop
        return None

    def workshop_at_anywhere(self):
        if self.settlement is None:
            return False
        return any(workshop.active for workshop in self.settlement.workshops)

    def farm_at(self, x, y):
        if self.settlement is None:
            return None
        for farm in self.settlement.farm_plots:
            if farm.active and (x, y) in farm.tiles:
                return farm
        return None

    def farm_at_origin(self, x, y):
        if self.settlement is None:
            return None
        for farm in self.settlement.farm_plots:
            if farm.active and farm.origin == (x, y):
                return farm
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
    settings: WorldGenSettings | None = None,
):
    from src.config import STARTING_AGENTS, WORLD_SEED

    base_settings = settings or default_worldgen_settings()
    effective_settings = base_settings.with_overrides(
        width=width if width is not None else base_settings.width,
        height=height if height is not None else base_settings.height,
        seed=seed if seed is not None else base_settings.seed if base_settings.seed is not None else WORLD_SEED,
    )

    world = World(
        effective_settings.width,
        effective_settings.height,
        seed=effective_settings.seed,
        settings=effective_settings,
    )
    world.generate()
    world.establish_settlement()
    world.spawn_agents(agent_count if agent_count is not None else STARTING_AGENTS)
    world.update_settlement_needs(force=True)
    world.update_resource_pressures()
    world.update_carrying_capacity()
    return world
