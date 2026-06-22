from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import TYPE_CHECKING

from src.config import (
    FARM_COMFORT_FOOD_DAYS,
    FARM_CREATION_MIN_DAY,
    FARM_FOOD_CAP,
    FARM_GROWTH_THRESHOLD,
    FARM_HARVEST_FOOD_PER_TILE,
    FARM_HARVEST_SEEDS_PER_TILE,
    FARM_MAX_PLOTS_LARGE,
    FARM_MAX_PLOTS_MEDIUM,
    FARM_MAX_PLOTS_SMALL,
    FARM_PLACEMENT_RADIUS_MARGIN,
    FARM_SEED_COST_PER_TILE,
    FARM_SEASON_GROWTH,
    FARM_START_FOOD_DAYS,
)
from src.environment_events import food_growth_event_multiplier
from src.workplace import DEFAULT_CAPACITY, FARM as FARM_WORKPLACE, Workplace

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"
FIELD_UNPREPARED = "Unprepared"
FIELD_PLANTED = "Planted"
FIELD_GROWING = "Growing"
FIELD_READY = "Ready For Harvest"
FIELD_DORMANT = "Dormant"

FARMABLE_TERRAIN = {
    "grass": 1.0,
    "plain": 0.95,
    "wetland": 0.85,
}


@dataclass
class FarmPlot:
    origin_x: int
    origin_y: int
    tiles: list[tuple[int, int]] = field(default_factory=list)
    growth: int = 0
    food: int = 0
    active: bool = True
    fertility: float = 1.0
    last_harvest_day: int = 0
    crop_state: str = FIELD_UNPREPARED
    seed_yield: int = 0

    def __post_init__(self):
        expected = farm_tiles(self.origin_x, self.origin_y)
        if not self.tiles:
            self.tiles = expected
        else:
            self.tiles = list(self.tiles)

        if sorted(self.tiles) != sorted(expected):
            raise ValueError("FarmPlot must own exactly the four tiles in its 2x2 footprint.")
        if self.food > 0:
            self.crop_state = FIELD_READY

    @property
    def origin(self) -> tuple[int, int]:
        return self.origin_x, self.origin_y


def farm_tiles(origin_x: int, origin_y: int) -> list[tuple[int, int]]:
    return [
        (origin_x, origin_y),
        (origin_x + 1, origin_y),
        (origin_x, origin_y + 1),
        (origin_x + 1, origin_y + 1),
    ]


def settlement_food_pressure(world: World) -> str:
    settlement = world.settlement
    if settlement is None:
        return LOW

    population = max(1, len(world.living_agents()) or settlement.population)
    stored_food = world.colony_storage.food
    ready_farm_food = sum(farm.food for farm in settlement.farm_plots if farm.active)
    local_food = len(getattr(settlement, "local_food", set()))
    winter_penalty = population if world.season == "Winter" else 0

    effective_food = stored_food + ready_farm_food + min(local_food, population * 3)
    if effective_food + winter_penalty <= population * FARM_START_FOOD_DAYS:
        return HIGH
    if effective_food + winter_penalty <= population * FARM_COMFORT_FOOD_DAYS:
        return MEDIUM
    return LOW


def max_farm_plots_for_population(population: int) -> int:
    if population <= 0:
        return 0
    if population <= 5:
        return FARM_MAX_PLOTS_SMALL
    if population <= 10:
        return FARM_MAX_PLOTS_MEDIUM
    return FARM_MAX_PLOTS_LARGE


def maybe_create_farm(world: World) -> FarmPlot | None:
    settlement = world.settlement
    if settlement is None or world.day < FARM_CREATION_MIN_DAY:
        return None
    pressure = settlement_food_pressure(world)
    if getattr(settlement, "farm_food_pressure", LOW) != pressure:
        settlement.farm_food_pressure = pressure
        world.log(f"Food Pressure: {pressure}")
    if pressure != HIGH:
        return None
    if len(settlement.farm_plots) >= max_farm_plots_for_population(settlement.population):
        return None

    site = find_farm_site_near_settlement(world)
    if site is None:
        return None

    farm = FarmPlot(site[0], site[1], fertility=farm_fertility(world, site[0], site[1]))
    settlement.farm_plots.append(farm)
    register_farm_workplace(world, farm)
    world.log("Farm creation triggered by high food pressure.")
    world.log("A 2x2 farm plot is marked near the settlement.")
    return farm


def register_farm_workplace(world: World, farm: FarmPlot):
    settlement = world.settlement
    if settlement is None:
        return
    farm_workplaces = settlement.workplaces_for_type(FARM_WORKPLACE)
    if farm_workplaces:
        workplace = farm_workplaces[0]
        for tile in farm.tiles:
            if tile not in workplace.tiles:
                workplace.tiles.append(tile)
        workplace.capacity = max(workplace.capacity, DEFAULT_CAPACITY[FARM_WORKPLACE])
        return
    settlement.workplaces.append(Workplace(
        workplace_id=f"farm-{len(farm_workplaces)}",
        workplace_type=FARM_WORKPLACE,
        x=farm.origin_x,
        y=farm.origin_y,
        capacity=DEFAULT_CAPACITY[FARM_WORKPLACE],
        tiles=list(farm.tiles),
    ))


def find_farm_site_near_settlement(world: World) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None

    radius = min(max(world.width, world.height), settlement.radius + FARM_PLACEMENT_RADIUS_MARGIN)
    candidates = []
    for y in range(max(0, settlement.y - radius), min(world.height - 1, settlement.y + radius + 1)):
        for x in range(max(0, settlement.x - radius), min(world.width - 1, settlement.x + radius + 1)):
            distance = max(abs(x - settlement.x), abs(y - settlement.y))
            if distance > radius:
                continue
            score = score_farm_site(world, x, y)
            if score < inf:
                candidates.append((score, distance, y, x))

    if not candidates:
        return None
    _, _, y, x = min(candidates)
    return x, y


def score_farm_site(world: World, origin_x: int, origin_y: int) -> float:
    if not is_valid_farm_site(world, origin_x, origin_y):
        return inf

    settlement = world.settlement
    if settlement is None:
        return 0

    center_x = origin_x + 0.5
    center_y = origin_y + 0.5
    hub_distance = max(abs(center_x - settlement.x), abs(center_y - settlement.y))
    manhattan = abs(center_x - settlement.x) + abs(center_y - settlement.y)

    score = hub_distance * 5 + manhattan
    if hub_distance < 3:
        score += 35
    elif 4 <= hub_distance <= settlement.radius:
        score -= 12

    score -= farm_fertility(world, origin_x, origin_y) * 12
    score -= min(_open_neighbors_around_plot(world, origin_x, origin_y), 8) * 2
    score -= _nearby_water_count(world, origin_x, origin_y, radius=4) * 1.5
    score += _nearby_special_count(world, origin_x, origin_y, radius=2) * 28
    score += _nearby_shelter_count(world, origin_x, origin_y, radius=1) * 20
    score += _nearby_farm_count(world, origin_x, origin_y, radius=1) * 35
    return score


def is_valid_farm_site(world: World, origin_x: int, origin_y: int) -> bool:
    return all(is_farmable_tile(world, x, y) for x, y in farm_tiles(origin_x, origin_y))


def is_farmable_tile(world: World, x: int, y: int) -> bool:
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    tile = world.tile_at(x, y)
    if not tile.walkable or tile.kind not in FARMABLE_TERRAIN:
        return False
    if world.agent_at(x, y) is not None:
        return False
    if world.stockpile_at(x, y) is not None or world.workshop_at(x, y) is not None:
        return False
    if world.farm_at(x, y) is not None:
        return False
    settlement = world.settlement
    if settlement is not None and (x, y) == (settlement.x, settlement.y):
        return False
    return True


def farm_fertility(world: World, origin_x: int, origin_y: int) -> float:
    values = [FARMABLE_TERRAIN.get(world.tile_at(x, y).kind, 0.0) for x, y in farm_tiles(origin_x, origin_y)]
    return sum(values) / 4


def update_farms(world: World):
    settlement = world.settlement
    if settlement is None:
        return

    for farm in settlement.farm_plots:
        if not farm.active:
            continue
        update_farm_cycle(world, farm)


def update_farm_cycle(world: World, farm: FarmPlot):
    if world.season == "Winter":
        if farm.food <= 0:
            farm.crop_state = FIELD_DORMANT
            farm.growth = 0
        return

    if world.season == "Spring":
        if farm.crop_state == FIELD_DORMANT:
            farm.crop_state = FIELD_UNPREPARED
            farm.growth = 0
        return

    if world.season == "Summer" and farm.crop_state in (FIELD_PLANTED, FIELD_GROWING):
        farm.crop_state = FIELD_GROWING
        farm.growth = min(FARM_GROWTH_THRESHOLD, farm.growth + daily_farm_growth(world, farm))
        return

    if world.season == "Autumn" and farm.crop_state in (FIELD_PLANTED, FIELD_GROWING):
        prepare_farm_harvest(world, farm)


def daily_farm_growth(world: World, farm: FarmPlot) -> int:
    base = FARM_SEASON_GROWTH.get(world.season, 20)
    terrain_multiplier = farm.fertility
    event_multiplier = sum(
        food_growth_event_multiplier(world.tile_at(x, y).kind, world.active_environment_events)
        for x, y in farm.tiles
    ) / 4
    return max(0, round(base * terrain_multiplier * event_multiplier))


def farm_seed_cost(farm: FarmPlot) -> int:
    return len(farm.tiles) * FARM_SEED_COST_PER_TILE


def farm_max_food_yield(farm: FarmPlot) -> int:
    return len(farm.tiles) * FARM_HARVEST_FOOD_PER_TILE


def farm_seed_yield(farm: FarmPlot) -> int:
    return len(farm.tiles) * FARM_HARVEST_SEEDS_PER_TILE


def farm_needs_planting(world: World, farm: FarmPlot) -> bool:
    return (
        world.season == "Spring"
        and farm.active
        and farm.crop_state in (FIELD_UNPREPARED, FIELD_DORMANT)
        and farm.food <= 0
    )


def farm_ready_to_harvest(farm: FarmPlot) -> bool:
    return farm.active and farm.crop_state == FIELD_READY and farm.food > 0


def farm_has_work(world: World, farm: FarmPlot) -> bool:
    return farm_needs_planting(world, farm) or farm_ready_to_harvest(farm)


def plant_farm(world: World, farm: FarmPlot) -> bool:
    if not farm_needs_planting(world, farm):
        return False
    cost = farm_seed_cost(farm)
    if world.colony_storage.withdraw_seeds(cost) < cost:
        return False
    farm.crop_state = FIELD_PLANTED
    farm.growth = 0
    farm.food = 0
    farm.seed_yield = 0
    return True


def prepare_farm_harvest(world: World, farm: FarmPlot):
    if farm.crop_state == FIELD_READY:
        return
    progress = max(0.25, min(1.0, farm.growth / FARM_GROWTH_THRESHOLD))
    farm.food = min(FARM_FOOD_CAP, max(1, round(farm_max_food_yield(farm) * progress)))
    farm.seed_yield = max(1, round(farm_seed_yield(farm) * progress))
    farm.crop_state = FIELD_READY
    farm.growth = FARM_GROWTH_THRESHOLD


def harvest_farm(world: World, farm: FarmPlot, amount: int = 1) -> int:
    if not farm_ready_to_harvest(farm):
        return 0
    harvested = min(max(0, amount), farm.food)
    farm.food -= harvested
    if harvested > 0:
        if farm.seed_yield > 0:
            world.colony_storage.deposit_seeds(farm.seed_yield)
            farm.seed_yield = 0
        farm.last_harvest_day = world.day
    if farm.food <= 0:
        farm.crop_state = FIELD_DORMANT if world.season == "Winter" else FIELD_UNPREPARED
        farm.growth = 0
    return harvested


def choose_farm_target(world: World, agent: Agent) -> FarmPlot | None:
    settlement = world.settlement
    if settlement is None:
        return None

    farms = [farm for farm in settlement.farm_plots if farm_ready_to_harvest(farm)]
    if not farms:
        return None

    from src.reservations import FARM

    available = [
        farm
        for farm in farms
        if not world.reservations.is_reserved(FARM, farm.origin, by_other_than=agent)
    ]
    if available:
        farms = available
    elif agent.hunger < 70:
        return None

    return min(
        farms,
        key=lambda farm: (
            min(abs(x - agent.x) + abs(y - agent.y) for x, y in farm.tiles),
            max(abs(farm.origin_x - settlement.x), abs(farm.origin_y - settlement.y)),
            farm.origin_y,
            farm.origin_x,
        ),
    )


def choose_farm_work_target(world: World, agent: Agent) -> FarmPlot | None:
    settlement = world.settlement
    if settlement is None:
        return None

    farms = [
        farm
        for farm in settlement.farm_plots
        if farm_has_work(world, farm)
    ]
    if not farms:
        return None
    farms = [
        farm
        for farm in farms
        if farm_ready_to_harvest(farm)
        or (farm_needs_planting(world, farm) and world.colony_storage.seed_reserve >= farm_seed_cost(farm))
    ]
    if not farms:
        return None

    return min(
        farms,
        key=lambda farm: (
            0 if farm_ready_to_harvest(farm) else 1,
            min(abs(x - agent.x) + abs(y - agent.y) for x, y in farm.tiles),
            farm.origin_y,
            farm.origin_x,
        ),
    )


def farm_border_edges(farm: FarmPlot, x: int, y: int) -> dict[str, bool]:
    return {
        "north": y == farm.origin_y,
        "south": y == farm.origin_y + 1,
        "west": x == farm.origin_x,
        "east": x == farm.origin_x + 1,
    }


def _open_neighbors_around_plot(world: World, origin_x: int, origin_y: int) -> int:
    plot_tiles = set(farm_tiles(origin_x, origin_y))
    neighbors = set()
    for x, y in plot_tiles:
        neighbors.update(((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)))

    count = 0
    for x, y in neighbors - plot_tiles:
        if not (0 <= x < world.width and 0 <= y < world.height):
            continue
        if world.tile_at(x, y).walkable and world.agent_at(x, y) is None:
            count += 1
    return count


def _nearby_water_count(world: World, origin_x: int, origin_y: int, radius: int) -> int:
    count = 0
    for y in range(max(0, origin_y - radius), min(world.height, origin_y + radius + 2)):
        for x in range(max(0, origin_x - radius), min(world.width, origin_x + radius + 2)):
            if max(abs(x - origin_x), abs(y - origin_y)) <= radius and world.tile_at(x, y).kind == "water":
                count += 1
    return count


def _nearby_special_count(world: World, origin_x: int, origin_y: int, radius: int) -> int:
    count = 0
    settlement = world.settlement
    for y in range(max(0, origin_y - radius), min(world.height, origin_y + radius + 2)):
        for x in range(max(0, origin_x - radius), min(world.width, origin_x + radius + 2)):
            if max(abs(x - origin_x), abs(y - origin_y)) > radius:
                continue
            if world.stockpile_at(x, y) is not None or world.workshop_at(x, y) is not None:
                count += 1
            if settlement is not None and (x, y) == (settlement.x, settlement.y):
                count += 1
    return count


def _nearby_shelter_count(world: World, origin_x: int, origin_y: int, radius: int) -> int:
    count = 0
    for y in range(max(0, origin_y - radius), min(world.height, origin_y + radius + 2)):
        for x in range(max(0, origin_x - radius), min(world.width, origin_x + radius + 2)):
            if world.tile_at(x, y).kind == "shelter":
                count += 1
    return count


def _nearby_farm_count(world: World, origin_x: int, origin_y: int, radius: int) -> int:
    count = 0
    for x, y in farm_tiles(origin_x, origin_y):
        for ny in range(max(0, y - radius), min(world.height, y + radius + 1)):
            for nx in range(max(0, x - radius), min(world.width, x + radius + 1)):
                if world.farm_at(nx, ny) is not None:
                    count += 1
    return count
