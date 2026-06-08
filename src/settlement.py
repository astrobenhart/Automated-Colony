from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from math import sqrt

from src.config import SETTLEMENT_EXPANDED_RESOURCE_RADIUS, SETTLEMENT_RADIUS, SETTLEMENT_RESOURCE_RADIUS, STOCKPILE_CAPACITY
from src.profiler import profiler
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT
from src.workshop import Workshop, create_workshops, is_workshop_tile

FOOD = "food"
WOOD = "wood"
WATER = "water"
LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"


@dataclass
class Stockpile:
    x: int
    y: int
    stockpile_type: str
    stored_amount: int = 0
    capacity: int = STOCKPILE_CAPACITY

    def deposit(self, amount: int) -> int:
        accepted = min(max(0, amount), max(0, self.capacity - self.stored_amount))
        self.stored_amount += accepted
        return accepted

    def withdraw(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.stored_amount)
        self.stored_amount -= withdrawn
        return withdrawn


@dataclass
class Settlement:
    name: str
    x: int
    y: int
    founded_day: int
    founded_season: str
    radius: int = SETTLEMENT_RADIUS
    resource_radius: int = SETTLEMENT_RESOURCE_RADIUS
    expanded_resource_radius: int = SETTLEMENT_EXPANDED_RESOURCE_RADIUS
    food_pressure: str = LOW
    wood_pressure: str = LOW
    water_pressure: str = LOW
    population: int = 0
    stockpiles: list[Stockpile] = field(default_factory=list)
    workshops: list[Workshop] = field(default_factory=list)
    activity_heatmap: dict[tuple[int, int], int] = field(default_factory=dict)
    local_food: set[tuple[int, int]] = field(default_factory=set)
    local_wood: set[tuple[int, int]] = field(default_factory=set)
    local_water: set[tuple[int, int]] = field(default_factory=set)
    local_resource_cache_day: int | None = None

    def record_activity(self, x: int, y: int):
        pos = (x, y)
        self.activity_heatmap[pos] = self.activity_heatmap.get(pos, 0) + 1

    def activity_at(self, x: int, y: int) -> int:
        return self.activity_heatmap.get((x, y), 0)

    def stockpile_for(self, stockpile_type: str) -> Stockpile | None:
        with profiler.time("stockpile logic"):
            for stockpile in self.stockpiles:
                if stockpile.stockpile_type == stockpile_type:
                    return stockpile
            return None


def found_settlement(world) -> Settlement:
    center_x, center_y = _agent_centroid(world.agents)
    x, y = nearest_walkable_tile(world, center_x, center_y)
    settlement = Settlement(
        name=settlement_name(world),
        x=x,
        y=y,
        founded_day=world.day,
        founded_season=world.season,
        population=len(world.living_agents()),
    )
    settlement.stockpiles = create_stockpiles(world, settlement)
    settlement.workshops = create_workshops(world, settlement)
    return settlement


def create_stockpiles(world, settlement: Settlement) -> list[Stockpile]:
    used = {(settlement.x, settlement.y)}
    stockpiles = []
    for stockpile_type in (FOOD, WOOD):
        pos = _nearest_stockpile_tile(world, settlement, used)
        if pos is None:
            continue
        used.add(pos)
        stockpiles.append(Stockpile(pos[0], pos[1], stockpile_type))
    return stockpiles


def _nearest_stockpile_tile(world, settlement: Settlement, used: set[tuple[int, int]]) -> tuple[int, int] | None:
    for radius in range(1, settlement.radius + 1):
        candidates = []
        for y in range(max(0, settlement.y - radius), min(world.height, settlement.y + radius + 1)):
            for x in range(max(0, settlement.x - radius), min(world.width, settlement.x + radius + 1)):
                if max(abs(x - settlement.x), abs(y - settlement.y)) != radius:
                    continue
                pos = (x, y)
                if pos in used:
                    continue
                if not world.tile_at(x, y).walkable:
                    continue
                if world.agent_at(x, y) is not None:
                    continue
                candidates.append(pos)

        if candidates:
            return min(candidates, key=lambda pos: (abs(pos[0] - settlement.x) + abs(pos[1] - settlement.y), pos[1], pos[0]))

    return None


def nearest_walkable_tile(world, center_x: int, center_y: int) -> tuple[int, int]:
    start_x = max(0, min(world.width - 1, center_x))
    start_y = max(0, min(world.height - 1, center_y))

    if world.tile_at(start_x, start_y).walkable:
        return start_x, start_y

    max_radius = max(world.width, world.height)
    for radius in range(1, max_radius + 1):
        candidates = []
        for y in range(max(0, start_y - radius), min(world.height, start_y + radius + 1)):
            for x in range(max(0, start_x - radius), min(world.width, start_x + radius + 1)):
                if max(abs(x - start_x), abs(y - start_y)) != radius:
                    continue
                if world.tile_at(x, y).walkable:
                    candidates.append((x, y))

        if candidates:
            return min(candidates, key=lambda pos: (abs(pos[0] - center_x) + abs(pos[1] - center_y), pos[1], pos[0]))

    return start_x, start_y


def distance_to_settlement(world, x: int, y: int) -> int | None:
    settlement = world.settlement
    if settlement is None:
        return None
    return max(abs(x - settlement.x), abs(y - settlement.y))


def is_near_settlement(world, x: int, y: int, radius: int | None = None) -> bool:
    settlement = world.settlement
    if settlement is None:
        return False
    active_radius = settlement.radius if radius is None else radius
    return distance_to_settlement(world, x, y) <= active_radius


def is_within_resource_radius(world, x: int, y: int, radius: int | None = None) -> bool:
    settlement = world.settlement
    if settlement is None:
        return False
    active_radius = settlement.resource_radius if radius is None else radius
    return distance_to_settlement(world, x, y) <= active_radius


def filter_positions_by_settlement_radius(world, positions: set[tuple[int, int]], radius: int | None = None) -> set[tuple[int, int]]:
    with profiler.time("settlement resource radius filtering"):
        return {pos for pos in positions if is_within_resource_radius(world, pos[0], pos[1], radius)}


def update_resource_pressures(world):
    settlement = world.settlement
    if settlement is None:
        return

    with profiler.time("settlement resource radius filtering"):
        refresh_local_resource_cache(world)
        settlement.food_pressure = resource_pressure(world, FOOD)
        settlement.wood_pressure = resource_pressure(world, WOOD)
        settlement.water_pressure = resource_pressure(world, WATER)


def resource_pressure(world, resource_type: str, agent=None) -> str:
    if resource_type == FOOD:
        local_food = _local_resource_count(world, FOOD)
        if (agent is not None and agent.hunger >= 70) or world.colony_storage.food <= 1 or local_food == 0:
            return HIGH
        if (agent is not None and agent.hunger >= 40) or world.colony_storage.food <= 4 or local_food <= 2:
            return MEDIUM
        return LOW

    if resource_type == WATER:
        local_water = _local_resource_count(world, WATER)
        if (agent is not None and agent.thirst >= 70) or local_water == 0:
            return HIGH
        if (agent is not None and agent.thirst >= 40) or local_water <= 2:
            return MEDIUM
        return LOW

    if resource_type == WOOD:
        local_wood = _local_resource_count(world, WOOD)
        if world.needs_more_shelters() or world.colony_storage.wood <= 1 or local_wood == 0:
            return HIGH
        if world.colony_storage.wood <= 5 or world.colony_storage.building_materials == 0 or local_wood <= 2:
            return MEDIUM
        return LOW

    return LOW


def resource_search_radius(world, resource_type: str, agent=None) -> int | None:
    settlement = world.settlement
    if settlement is None:
        return None

    pressure = resource_pressure(world, resource_type, agent)
    _set_pressure(settlement, resource_type, pressure)

    if _is_urgent_need(agent, resource_type) or pressure == HIGH:
        return None
    if pressure == MEDIUM:
        return settlement.expanded_resource_radius
    return settlement.resource_radius


def choose_resource_target(world, agent, resource_type: str, candidates: set[tuple[int, int]]) -> tuple[int, int] | None:
    with profiler.time("resource target selection"):
        if not candidates:
            return None

        settlement = world.settlement
        pressure = resource_pressure(world, resource_type, agent)
        if settlement is not None:
            _set_pressure(settlement, resource_type, pressure)

        return min(
            candidates,
            key=lambda pos: (
                _resource_score(world, agent, resource_type, pos, pressure),
                distance_to_settlement(world, pos[0], pos[1]) or 0,
                pos[1],
                pos[0],
            ),
        )


def exploration_radius_for_role(role: str, settlement_radius: int) -> int:
    if role == SCOUT:
        return settlement_radius * 2
    if role == FORAGER:
        return max(3, round(settlement_radius * 0.85))
    if role == BUILDER:
        return max(3, round(settlement_radius * 0.75))
    if role == GENERALIST:
        return settlement_radius
    return settlement_radius


def _local_resource_count(world, resource_type: str) -> int:
    settlement = world.settlement
    if settlement is None:
        return 0

    refresh_local_resource_cache(world)
    if resource_type == FOOD:
        return len(settlement.local_food)
    if resource_type == WOOD:
        return len(settlement.local_wood)
    if resource_type == WATER:
        return len(settlement.local_water)
    return 0


def refresh_local_resource_cache(world, force: bool = False):
    settlement = world.settlement
    if settlement is None:
        return
    if not force and settlement.local_resource_cache_day == world.day:
        return

    local_food: set[tuple[int, int]] = set()
    local_wood: set[tuple[int, int]] = set()
    local_water: set[tuple[int, int]] = set()
    for y in range(max(0, settlement.y - settlement.resource_radius), min(world.height, settlement.y + settlement.resource_radius + 1)):
        for x in range(max(0, settlement.x - settlement.resource_radius), min(world.width, settlement.x + settlement.resource_radius + 1)):
            if distance_to_settlement(world, x, y) > settlement.resource_radius:
                continue
            tile = world.tile_at(x, y)
            pos = (x, y)
            if tile.food > 0:
                local_food.add(pos)
            if tile.wood > 0:
                local_wood.add(pos)
            if tile.kind == "water":
                local_water.add(pos)
    settlement.local_food = local_food
    settlement.local_wood = local_wood
    settlement.local_water = local_water
    settlement.local_resource_cache_day = world.day


def _resource_score(world, agent, resource_type: str, pos: tuple[int, int], pressure: str) -> float:
    manhattan = abs(pos[0] - agent.x) + abs(pos[1] - agent.y)
    chebyshev = max(abs(pos[0] - agent.x), abs(pos[1] - agent.y))
    euclidean = sqrt((pos[0] - agent.x) ** 2 + (pos[1] - agent.y) ** 2)
    local_penalty = _locality_penalty(world, agent, resource_type, pos, pressure)
    return manhattan + (chebyshev * 0.25) + (euclidean * 0.1) + local_penalty


def _set_pressure(settlement: Settlement, resource_type: str, pressure: str):
    if resource_type == FOOD:
        settlement.food_pressure = pressure
    elif resource_type == WOOD:
        settlement.wood_pressure = pressure
    elif resource_type == WATER:
        settlement.water_pressure = pressure


def _is_urgent_need(agent, resource_type: str) -> bool:
    if agent is None:
        return False
    if resource_type == FOOD:
        return agent.hunger >= 70
    if resource_type == WATER:
        return agent.thirst >= 70
    return False


def _locality_penalty(world, agent, resource_type: str, pos: tuple[int, int], pressure: str) -> float:
    settlement = world.settlement
    if settlement is None:
        return 0

    distance = distance_to_settlement(world, pos[0], pos[1])
    if distance is None:
        return 0

    if distance <= settlement.resource_radius:
        penalty = 0
    elif distance <= settlement.expanded_resource_radius:
        penalty = 12 if pressure == LOW else 7 if pressure == MEDIUM else 2
    else:
        penalty = 30 if pressure == LOW else 18 if pressure == MEDIUM else 6

    if agent.role == SCOUT:
        penalty *= 0.25
    elif agent.role == FORAGER and resource_type == FOOD:
        penalty *= 1.25
    elif agent.role == BUILDER and resource_type == WOOD:
        penalty *= 1.25

    if _is_urgent_need(agent, resource_type):
        penalty *= 0.2

    return penalty


def random_tile_near_settlement(world, rng=None, role: str | None = None) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None
    if rng is None:
        rng = random

    radius = exploration_radius_for_role(role or GENERALIST, settlement.radius)
    candidates = _walkable_tiles_in_radius(world, settlement.x, settlement.y, radius)
    candidates = [
        pos for pos in candidates
        if (
            pos != (settlement.x, settlement.y)
            and not is_stockpile_tile(world, pos[0], pos[1])
            and not is_workshop_tile(world, pos[0], pos[1])
            and world.agent_at(pos[0], pos[1]) is None
        )
    ]

    if not candidates:
        return None

    return rng.choice(candidates)


def valid_build_tile_near_settlement(world, agent=None) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None

    candidates = []
    for x, y in _walkable_tiles_in_radius(world, settlement.x, settlement.y, settlement.radius):
        if agent is not None and (x, y) == (agent.x, agent.y):
            occupied = False
        else:
            occupied = world.agent_at(x, y) is not None

        if occupied:
            continue

        tile = world.tile_at(x, y)
        if (
            tile.kind == "grass"
            and (x, y) != (settlement.x, settlement.y)
            and not is_stockpile_tile(world, x, y)
            and not is_workshop_tile(world, x, y)
        ):
            candidates.append((x, y))

    if not candidates:
        return None

    return min(candidates, key=lambda pos: (abs(pos[0] - settlement.x) + abs(pos[1] - settlement.y), pos[1], pos[0]))


def stockpile_for(world, stockpile_type: str) -> Stockpile | None:
    settlement = world.settlement
    if settlement is None:
        return None
    return settlement.stockpile_for(stockpile_type)


def is_stockpile_tile(world, x: int, y: int) -> bool:
    with profiler.time("stockpile logic"):
        settlement = world.settlement
        if settlement is None:
            return False
        return any(stockpile.x == x and stockpile.y == y for stockpile in settlement.stockpiles)


def is_adjacent_to_stockpile(world, x: int, y: int, stockpile_type: str) -> bool:
    with profiler.time("stockpile logic"):
        stockpile = stockpile_for(world, stockpile_type)
        if stockpile is None:
            return False
        return max(abs(x - stockpile.x), abs(y - stockpile.y)) <= 1


def stockpile_access_tile(world, stockpile_type: str, agent=None) -> tuple[int, int] | None:
    with profiler.time("stockpile logic"):
        stockpile = stockpile_for(world, stockpile_type)
        if stockpile is None:
            return None

        candidates = []
        for y in range(max(0, stockpile.y - 1), min(world.height, stockpile.y + 2)):
            for x in range(max(0, stockpile.x - 1), min(world.width, stockpile.x + 2)):
                if (x, y) == (stockpile.x, stockpile.y):
                    continue
                if not world.tile_at(x, y).walkable:
                    continue
                if agent is not None and (x, y) == (agent.x, agent.y):
                    occupied = False
                else:
                    occupied = world.agent_at(x, y) is not None
                if not occupied:
                    candidates.append((x, y))

        if not candidates:
            return None

        return min(candidates, key=lambda pos: (abs(pos[0] - stockpile.x) + abs(pos[1] - stockpile.y), pos[1], pos[0]))


def deposit_to_stockpile(world, stockpile_type: str, amount: int) -> int:
    stockpile = stockpile_for(world, stockpile_type)
    if stockpile is None:
        return 0
    return stockpile.deposit(amount)


def withdraw_from_stockpile(world, stockpile_type: str, amount: int) -> int:
    stockpile = stockpile_for(world, stockpile_type)
    if stockpile is None:
        return 0
    return stockpile.withdraw(amount)


def settlement_name(world) -> str:
    identity = world.identity
    title = identity.title if identity is not None else "Colony"
    tags = identity.tags if identity is not None else []
    root = _name_root(title)

    suffixes = _suffixes_for_tags(tags)
    suffix = suffixes[_deterministic_index(world.seed, title, tags, len(suffixes))]
    return f"{root}{suffix}"


def _walkable_tiles_in_radius(world, center_x: int, center_y: int, radius: int) -> list[tuple[int, int]]:
    tiles = []
    for y in range(max(0, center_y - radius), min(world.height, center_y + radius + 1)):
        for x in range(max(0, center_x - radius), min(world.width, center_x + radius + 1)):
            if max(abs(x - center_x), abs(y - center_y)) > radius:
                continue
            if world.tile_at(x, y).walkable:
                tiles.append((x, y))
    return tiles


def _agent_centroid(agents) -> tuple[int, int]:
    if not agents:
        return 0, 0

    x = round(sum(agent.x for agent in agents) / len(agents))
    y = round(sum(agent.y for agent in agents) / len(agents))
    return x, y


def _name_root(title: str) -> str:
    first_word = title.replace("The ", "").split()[0]
    for suffix in ("mere", "vein", "scar", "wood", "deep", "stone", "water", "fen"):
        if first_word.lower().endswith(suffix):
            return first_word[:-len(suffix)].capitalize() or first_word
    return first_word.capitalize()


def _suffixes_for_tags(tags: list[str]) -> list[str]:
    if "marshland" in tags or "wet" in tags:
        return ["haven", "watch", "mere"]
    if "forested" in tags:
        return ["hold", "watch", "haven"]
    if "dry" in tags or "thirsty" in tags:
        return ["hold", "watch", "rest"]
    if "mountainous" in tags or "rugged" in tags:
        return ["watch", "hold", "crest"]
    if "harsh" in tags or "resource_poor" in tags:
        return ["watch", "hold", "haven"]
    return ["hold", "haven", "watch"]


def _deterministic_index(seed, title: str, tags: list[str], count: int) -> int:
    key = f"{seed}|{title}|{','.join(tags)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % count
