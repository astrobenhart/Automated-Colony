import random
import time
from dataclasses import dataclass, field

from src.building_priorities import highest_priority, needed_shelters, update_settlement_needs
from src.appearance import appearance_seed_for, appearance_type_for_seed
from src.carrying_capacity import carrying_capacity_report
from src.colony_memory import ColonyMemory
from src.colony_storage import ColonyStorage
from src.environment_events import update_environment_events
from src.farming import maybe_create_farm, update_farms
from src.history_seed import seed_starting_chronicle
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
from src.lifecycle import demographic_profiles, profile_for_stage, ADULT, OLDER_ADULT
from src.roles import role_for_index
from src.scenarios import scenario_for_key, starting_population_for_scenario
from src.simulation_lod import (
    LODProfileStat,
    LOD_1_TASKS,
    LOD_2_NEEDS,
    LOD_3_SOCIAL,
    LOD_4_PLANNING,
    LOD_5_HISTORY,
    tier_names,
)
from src.partnerships import update_partnerships
from src.social_memory import update_household_familiarity, update_social_memory
from src.social_seed import seed_preexisting_social_history
from src.traits import trait_for_index
from src.task_behavior import assign_daily_role, run_villager_task
from src.settlement_planner import plan_settlement_work
from src.village_paths import decay_foot_traffic
from src.settlement import (
    Settlement,
    choose_resource_target,
    distance_to_settlement,
    filter_positions_by_settlement_radius,
    found_settlement,
    is_within_resource_radius,
    resource_search_radius,
    update_resource_pressures,
    withdraw_from_stockpile,
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
    villager_update_cursor: int = 0
    last_tick_ms: float = 0.0
    last_villager_ms: float = 0.0
    last_settlement_ms: float = 0.0
    last_updated_villagers: int = 0
    pathfinding_calls: int = 0
    lod_stats: dict[str, LODProfileStat] = field(
        default_factory=lambda: {tier: LODProfileStat() for tier in tier_names()}
    )

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

        from src.config import HOME_WANDER_MAX_RADIUS, HOME_WANDER_MIN_RADIUS

        names = [
            "Ari", "Bryn", "Cato", "Dara", "Eli",
            "Fenn", "Gala", "Hale", "Ira", "Juno",
        ]

        positions = self.initial_spawn_positions(amount)
        home_assignments = self.initial_home_assignments(amount)
        scenario_key = getattr(self.settlement, "scenario_key", None)
        profiles = demographic_profiles(amount, self.seed, scenario_key=scenario_key)
        home_settlement_id = self.settlement.settlement_id if self.settlement is not None else None
        home_settlement_name = self.settlement.name if self.settlement is not None else None
        for i, (x, y) in enumerate(positions):
            appearance_seed = appearance_seed_for(self.seed, i, names[i % len(names)])
            home = home_assignments[i] if i < len(home_assignments) else None
            home_x, home_y = (home.x, home.y) if home is not None else (None, None)
            household = self.household_for_home(home.home_id if home is not None else None)
            rng = random.Random(f"{self.seed}|villager-idle|{i}")
            profile = profiles[i]
            agent = Agent(
                names[i % len(names)],
                x,
                y,
                role=role_for_index(i),
                lifecycle_stage=profile.lifecycle_stage,
                age=profile.age,
                experience_level=profile.experience_level,
                trait=trait_for_index(i),
                agent_id=f"villager-{i}",
                appearance_seed=appearance_seed,
                appearance_type=appearance_type_for_seed(appearance_seed),
                home_settlement_id=home_settlement_id,
                home_settlement_name=home_settlement_name,
                household_id=household.household_id if household is not None else None,
                home_id=home.home_id if home is not None else None,
                home_x=home_x,
                home_y=home_y,
                birth_settlement_id=home_settlement_id,
                birth_settlement_name=home_settlement_name,
                birth_year=self.year - profile.age,
                birth_day=1,
                idle_until_tick=rng.randint(0, 3),
                home_wander_radius=rng.randint(HOME_WANDER_MIN_RADIUS, HOME_WANDER_MAX_RADIUS),
            )
            self.add_agent_to_household(agent, household)
            assign_daily_role(agent, self)
            self.assign_agent_workplace(agent)
            self.agents.append(agent)

        self.seed_household_age_variation()
        seed_preexisting_social_history(self)
        self.update_settlement_population()
        self.log(f"{amount} villagers enter the world.")

    def initial_home_assignments(self, amount):
        settlement = self.settlement
        if amount <= 0 or settlement is None or not settlement.homes:
            return []

        rng = random.Random(f"{self.seed}|{settlement.settlement_id}|home-assignment|{amount}")
        assignments = []
        homes = list(settlement.homes)
        rng.shuffle(homes)
        assignments.extend(homes[:amount])
        while len(assignments) < amount:
            assignments.append(rng.choice(settlement.homes))
        rng.shuffle(assignments)
        return assignments

    def establish_settlement(self):
        self.settlement = found_settlement(self)

    def initial_spawn_positions(self, amount):
        from src.config import INITIAL_SPAWN_MAX_RADIUS, INITIAL_SPAWN_RADIUS

        if amount <= 0:
            return []
        if self.settlement is None:
            return self._fallback_spawn_positions(amount)
        if self.settlement.homes:
            positions = self._home_spawn_positions(amount)
            if len(positions) == amount:
                return positions

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

    def _home_spawn_positions(self, amount):
        settlement = self.settlement
        if settlement is None or not settlement.homes:
            return []

        rng = random.Random(f"{self.seed}|{settlement.settlement_id}|home-spawn|{amount}")
        home_positions = [(home.x, home.y) for home in settlement.homes]
        positions = []

        for _ in range(amount):
            home_x, home_y = rng.choice(home_positions)
            candidates = self._home_spawn_candidates(home_x, home_y)
            if candidates:
                positions.append(rng.choice(candidates))

        return positions

    def _home_spawn_candidates(self, home_x, home_y):
        candidates = []
        for dy in (0, 1, -1):
            for dx in (0, 1, -1):
                x = home_x + dx
                y = home_y + dy
                if self.is_valid_spawn_tile(x, y):
                    distance = max(abs(dx), abs(dy))
                    candidates.append((distance, y, x))

        return [(x, y) for _, y, x in sorted(candidates)]

    def household_for_home(self, home_id):
        if self.settlement is None:
            return None
        return self.settlement.household_for_home(home_id)

    def household_for_agent(self, agent):
        if self.settlement is None:
            return None
        return self.settlement.household_for(getattr(agent, "household_id", None))

    def add_agent_to_household(self, agent, household):
        if household is None:
            return
        agent_id = agent.agent_id or agent.name
        if self.settlement is not None:
            for other_household in self.settlement.households:
                if other_household is not household and agent_id in other_household.member_ids:
                    other_household.member_ids.remove(agent_id)

        household.add_member(agent_id)
        agent.household_id = household.household_id
        agent.home_id = household.home_id
        home = self.settlement.home_for_id(household.home_id) if self.settlement is not None else None
        if home is not None:
            agent.home_x = home.x
            agent.home_y = home.y

    def ensure_household_membership(self):
        if self.settlement is None or not self.settlement.households:
            return

        default_household = self.settlement.households[0]
        for agent in self.living_agents():
            household = self.household_for_agent(agent)
            if household is None:
                home_household = self.household_for_home(getattr(agent, "home_id", None))
                household = home_household or default_household
            self.add_agent_to_household(agent, household)

    def seed_household_age_variation(self):
        if self.settlement is None:
            return

        agents_by_id = {
            agent.agent_id or agent.name: agent
            for agent in self.agents
        }
        for household in self.settlement.households:
            members = [
                agents_by_id[member_id]
                for member_id in household.member_ids
                if member_id in agents_by_id
            ]
            if members:
                head = max(members, key=lambda agent: (agent.age, agent.agent_id or agent.name))
                household.household_head = head.agent_id or head.name
            if len(members) < 2:
                continue
            if len({member.lifecycle_stage for member in members}) > 1:
                continue

            target_stage = OLDER_ADULT if members[0].lifecycle_stage == ADULT else ADULT
            rng = random.Random(f"{self.seed}|{household.household_id}|age-spread")
            profile = profile_for_stage(target_stage, rng)
            adjusted_member = sorted(members, key=lambda agent: (agent.age, agent.agent_id or agent.name))[-1]
            adjusted_member.lifecycle_stage = profile.lifecycle_stage
            adjusted_member.age = profile.age
            adjusted_member.experience_level = profile.experience_level
            head = max(members, key=lambda agent: (agent.age, agent.agent_id or agent.name))
            household.household_head = head.agent_id or head.name

    def assign_agent_workplace(self, agent):
        workplace = self.preferred_workplace_for_agent(agent)
        if workplace is None:
            return
        agent_id = agent.agent_id or agent.name
        if workplace.assign_worker(agent_id):
            agent.workplace_id = workplace.workplace_id

    def preferred_workplace_for_agent(self, agent):
        if self.settlement is None:
            return None
        from src.roles import BUILDER, FORAGER, SCOUT
        from src.workplace import FARM, STORAGE, VILLAGE_CENTER, WORKSHOP

        if agent.role == FORAGER:
            types = (FARM, STORAGE, VILLAGE_CENTER)
        elif agent.role == BUILDER:
            types = (WORKSHOP, STORAGE, VILLAGE_CENTER)
        elif agent.role == SCOUT:
            types = (VILLAGE_CENTER,)
        else:
            types = (STORAGE, FARM, VILLAGE_CENTER)

        for workplace_type in types:
            candidates = [
                workplace
                for workplace in self.settlement.workplaces_for_type(workplace_type)
                if len(workplace.assigned_workers) < workplace.capacity
            ]
            if candidates:
                return min(candidates, key=lambda workplace: (len(workplace.assigned_workers), workplace.y, workplace.x))
        return None

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
            tick_start = time.perf_counter()
            self.tick += 1
            self.reservations.cleanup(self)

            settlement_seconds = 0.0
            from src.config import TICKS_PER_DAY, TICKS_PER_HOUR
            if self.tick % TICKS_PER_DAY == 0:
                scheduled_start = time.perf_counter()
                self.advance_day()
                settlement_seconds += time.perf_counter() - scheduled_start
            elif self.tick % TICKS_PER_HOUR == 0:
                self.run_hourly_updates()

            villager_start = time.perf_counter()
            updated_count = self.update_villagers_for_tick()
            villager_seconds = time.perf_counter() - villager_start
            self.record_lod_update(LOD_1_TASKS, villager_seconds)
            self.log_performance_tick(tick_start, villager_seconds, settlement_seconds, updated_count)

    def update_villagers_for_tick(self) -> int:
        living = self.living_agents()
        if not living:
            self.villager_update_cursor = 0
            return 0

        from src.config import MAX_UPDATES_PER_TICK
        updates = min(MAX_UPDATES_PER_TICK, len(living))
        start_index = self.villager_update_cursor % len(living)

        for offset in range(updates):
            agent = living[(start_index + offset) % len(living)]
            self.update_villager(agent)

        self.villager_update_cursor = (start_index + updates) % len(living)
        return updates

    def update_villager(self, agent: Agent):
        if run_villager_task(agent, self):
            agent.die_if_needed(self)
            return

        progress_before = agent.progress_snapshot(self)
        action = agent.action_for_tick(self)
        action.execute(agent, self)
        agent.die_if_needed(self)
        if agent.alive:
            agent.update_progress_tracking(self, progress_before)
            if agent.current_action == "Recovering":
                agent.release_reservations(self)

    def log_performance_tick(
        self,
        tick_start: float,
        villager_seconds: float,
        settlement_seconds: float,
        updated_count: int,
    ):
        self.last_tick_ms = (time.perf_counter() - tick_start) * 1000
        self.last_villager_ms = villager_seconds * 1000
        self.last_settlement_ms = settlement_seconds * 1000
        self.last_updated_villagers = updated_count

    def run_hourly_updates(self):
        from src.config import TICKS_PER_HOUR

        needs_start = time.perf_counter()
        self.update_needs_for_lod(TICKS_PER_HOUR)
        update_wildlife(self, random)
        self.record_lod_update(LOD_2_NEEDS, time.perf_counter() - needs_start)

    def update_needs_for_lod(self, elapsed_ticks: int):
        living = self.living_agents()
        if not living:
            return

        from src.config import MAX_UPDATES_PER_TICK
        active_fraction = min(MAX_UPDATES_PER_TICK, len(living)) / len(living)
        scaled_ticks = elapsed_ticks * active_fraction
        for agent in living:
            agent.update_needs(scaled_ticks)

    def run_daily_settlement_updates(self):
        settlement_start = time.perf_counter()
        self.update_settlement_population()
        self.update_settlement_needs(force=True)
        self.update_resource_pressures()
        self.update_carrying_capacity()
        self.record_settlement_activity()
        elapsed = time.perf_counter() - settlement_start
        self.log_settlement_performance(elapsed)
        self.record_lod_update(LOD_4_PLANNING, elapsed)

    def log_settlement_performance(self, seconds: float):
        self.last_settlement_ms = seconds * 1000

    def run_startup_settlement_updates(self):
        self.run_daily_settlement_updates()
        plan_start = time.perf_counter()
        self.plan_settlement_work()
        self.record_lod_update(LOD_4_PLANNING, time.perf_counter() - plan_start)

    def run_daily_updates(self):
        from src.config import TICKS_PER_HOUR

        needs_start = time.perf_counter()
        self.update_needs_for_lod(TICKS_PER_HOUR)
        update_wildlife(self, random)
        self.record_lod_update(LOD_2_NEEDS, time.perf_counter() - needs_start)

        planning_start = time.perf_counter()
        update_environment_events(self, random)
        decay_foot_traffic(self)
        self.age_stored_food()
        self.regrow_resources()
        update_farms(self)
        self.record_lod_update(LOD_4_PLANNING, time.perf_counter() - planning_start)

        self.run_daily_settlement_updates()
        planning_start = time.perf_counter()
        maybe_create_farm(self)
        self.update_carrying_capacity()
        self.plan_settlement_work()
        self.record_lod_update(LOD_4_PLANNING, time.perf_counter() - planning_start)

        social_start = time.perf_counter()
        update_social_memory(self)
        self.ensure_household_membership()
        update_household_familiarity(self)
        update_partnerships(self)
        update_influence_peaks(self)
        self.record_lod_update(LOD_3_SOCIAL, time.perf_counter() - social_start)

        history_start = time.perf_counter()
        expire_remembrances(self)
        self.record_lod_update(LOD_5_HISTORY, time.perf_counter() - history_start)

    def assign_daily_roles(self):
        for agent in self.living_agents():
            assign_daily_role(agent, self)

    def plan_settlement_work(self):
        plan_settlement_work(self)

    def record_lod_update(self, tier: str, seconds: float):
        stat = self.lod_stats.setdefault(tier, LODProfileStat())
        stat.record(seconds)

    def lod_report(self) -> list[tuple[str, int, float, float, float]]:
        rows = [
            (tier, stat.calls, stat.last_seconds, stat.average_seconds, stat.total_seconds)
            for tier, stat in self.lod_stats.items()
        ]
        return sorted(rows, key=lambda row: row[4], reverse=True)

    def advance_day(self):
        self.day += 1
        if should_advance_season(self.day):
            self.advance_season()

        self.run_daily_updates()
        self.log(f"Day {self.day} begins.")

    def advance_season(self):
        self.season_index = next_season_index(self.season_index)
        self.log(f"{self.season} begins.")

    def regrow_resources(self):
        for row in self.tiles:
            for tile in row:
                apply_resource_ecology(tile, self.season, random, self.active_environment_events, self.settings)

    def age_stored_food(self):
        from src.settlement import FOOD

        spoiled = self.colony_storage.age_food()
        if spoiled <= 0:
            return
        withdraw_from_stockpile(self, FOOD, spoiled)
        self.log(f"{spoiled} stored food spoils.")

    def living_agents(self):
        return [agent for agent in self.agents if agent.alive]

    def tile_at(self, x, y):
        return self.tiles[y][x]

    def can_move_to(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        if not self.tile_at(x, y).walkable:
            return False

        return True

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

    def workplace_at(self, x, y):
        if self.settlement is None:
            return None
        for workplace in self.settlement.workplaces:
            if (x, y) in workplace.tiles:
                return workplace
        return None

    def home_at(self, x, y):
        if self.settlement is None:
            return None
        for home in self.settlement.homes:
            if home.x == x and home.y == y:
                return home
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
    scenario = scenario_for_key(effective_settings.scenario)
    starting_agents = starting_population_for_scenario(
        scenario,
        effective_settings.seed,
        agent_count,
        STARTING_AGENTS,
    )
    apply_scenario_reserves(world, scenario)
    world.spawn_agents(starting_agents)
    world.run_startup_settlement_updates()
    seed_starting_chronicle(world)
    return world


def apply_scenario_reserves(world: World, scenario):
    reserve = scenario.reserve
    if reserve.food:
        world.colony_storage.deposit_food(reserve.food)
    if reserve.water:
        world.colony_storage.deposit_water(reserve.water)
    if reserve.wood:
        world.colony_storage.deposit_wood(reserve.wood)
    if reserve.seeds is not None:
        world.colony_storage.seed_reserve = reserve.seeds
