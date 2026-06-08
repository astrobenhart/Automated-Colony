from __future__ import annotations

from math import inf
from typing import TYPE_CHECKING

from src.building_priorities import SHELTER

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


BUILDABLE_TERRAIN = {
    SHELTER: {"grass"},
}


def is_buildable_tile(world: World, x: int, y: int, building_type: str) -> bool:
    if not _in_bounds(world, x, y):
        return False
    if world.agent_at(x, y) is not None:
        return False
    return _is_base_buildable_tile(world, x, y, building_type)


def score_build_site(world: World, x: int, y: int, building_type: str) -> float:
    if not is_buildable_tile(world, x, y, building_type):
        return inf
    return _score_build_site(world, x, y, building_type)


def find_build_site_near_settlement(world: World, building_type: str, agent: Agent | None = None) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None

    local = _best_site_in_radius(world, building_type, settlement.radius, agent)
    if local is not None:
        return local

    broader_radius = min(max(world.width, world.height), settlement.radius + 4)
    return _best_site_in_radius(world, building_type, broader_radius, agent)


def near_existing_building(world: World, x: int, y: int, building_type: str | None = None) -> bool:
    for bx, by in _existing_buildings_near_settlement(world, building_type):
        distance = max(abs(x - bx), abs(y - by))
        if 1 <= distance <= 3:
            return True
    return False


def would_block_access(world: World, x: int, y: int) -> bool:
    if _open_cardinal_neighbors(world, x, y, blocked={(x, y)}) < 2:
        return True

    for ix, iy in _important_tiles(world):
        if max(abs(x - ix), abs(y - iy)) > 1:
            continue
        if _open_cardinal_neighbors(world, ix, iy, blocked={(x, y)}) < 2:
            return True

    return False


def _best_site_in_radius(
    world: World,
    building_type: str,
    radius: int,
    agent: Agent | None,
) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None

    candidates: list[tuple[float, int, int, tuple[int, int]]] = []
    existing = list(_existing_buildings_near_settlement(world, building_type))
    for y in range(max(0, settlement.y - radius), min(world.height, settlement.y + radius + 1)):
        for x in range(max(0, settlement.x - radius), min(world.width, settlement.x + radius + 1)):
            hub_distance = max(abs(x - settlement.x), abs(y - settlement.y))
            if hub_distance > radius:
                continue
            if not _candidate_buildable_for_agent(world, x, y, building_type, agent):
                continue
            score = _score_build_site(world, x, y, building_type, existing)
            candidates.append((score, hub_distance, y, (x, y)))

    if not candidates:
        return None
    return min(candidates)[3]


def _candidate_buildable_for_agent(
    world: World,
    x: int,
    y: int,
    building_type: str,
    agent: Agent | None,
) -> bool:
    occupant = world.agent_at(x, y)
    if occupant is not None and occupant is not agent:
        return False
    return _is_base_buildable_tile(world, x, y, building_type)


def _is_base_buildable_tile(world: World, x: int, y: int, building_type: str) -> bool:
    if not _in_bounds(world, x, y):
        return False

    tile = world.tile_at(x, y)
    if tile.kind not in BUILDABLE_TERRAIN.get(building_type, {"grass"}):
        return False
    if world.stockpile_at(x, y) is not None:
        return False
    if world.workshop_at(x, y) is not None:
        return False

    settlement = world.settlement
    if settlement is not None and (x, y) == (settlement.x, settlement.y):
        return False

    return True


def _score_build_site(
    world: World,
    x: int,
    y: int,
    building_type: str,
    existing: list[tuple[int, int]] | None = None,
) -> float:
    settlement = world.settlement
    if settlement is None:
        return 0

    score = max(abs(x - settlement.x), abs(y - settlement.y)) * 4
    score += abs(x - settlement.x) + abs(y - settlement.y)

    if existing is None:
        existing = list(_existing_buildings_near_settlement(world, building_type))
    if existing:
        nearest = min(max(abs(x - bx), abs(y - by)) for bx, by in existing)
        if nearest == 0:
            return inf
        if nearest == 1:
            score += 60
        elif nearest in (2, 3):
            score -= 40
        elif nearest <= 5:
            score -= 15
        else:
            score += nearest * 8
    else:
        hub_distance = max(abs(x - settlement.x), abs(y - settlement.y))
        if 2 <= hub_distance <= 4:
            score -= 6
        future_options = _future_cluster_options(world, x, y, building_type)
        if future_options == 0:
            score += 80
        else:
            score -= min(future_options, 4) * 8

    adjacent_shelters = _neighbor_building_count(world, x, y, SHELTER, radius=1)
    nearby_shelters = _neighbor_building_count(world, x, y, SHELTER, radius=2)
    score += adjacent_shelters * 50
    score += max(0, nearby_shelters - 3) * 8

    open_neighbors = _open_cardinal_neighbors(world, x, y, blocked={(x, y)})
    if open_neighbors < 2:
        score += 40
    else:
        score -= open_neighbors * 2

    if would_block_access(world, x, y):
        score += 50

    score += _adjacent_special_count(world, x, y) * 25
    return score


def _existing_buildings_near_settlement(world: World, building_type: str | None = None):
    settlement = world.settlement
    if settlement is None:
        return

    radius = min(max(world.width, world.height), settlement.radius + 4)
    for y in range(max(0, settlement.y - radius), min(world.height, settlement.y + radius + 1)):
        for x in range(max(0, settlement.x - radius), min(world.width, settlement.x + radius + 1)):
            if max(abs(x - settlement.x), abs(y - settlement.y)) > radius:
                continue
            tile = world.tile_at(x, y)
            if building_type is None:
                if tile.kind == SHELTER:
                    yield x, y
            elif tile.kind == building_type:
                yield x, y


def _neighbor_building_count(world: World, x: int, y: int, building_type: str, radius: int) -> int:
    count = 0
    for ny in range(max(0, y - radius), min(world.height, y + radius + 1)):
        for nx in range(max(0, x - radius), min(world.width, x + radius + 1)):
            if (nx, ny) == (x, y):
                continue
            if max(abs(nx - x), abs(ny - y)) > radius:
                continue
            if world.tile_at(nx, ny).kind == building_type:
                count += 1
    return count


def _future_cluster_options(world: World, x: int, y: int, building_type: str) -> int:
    options = 0
    for ny in range(max(0, y - 3), min(world.height, y + 4)):
        for nx in range(max(0, x - 3), min(world.width, x + 4)):
            distance = max(abs(nx - x), abs(ny - y))
            if distance not in (2, 3):
                continue
            if _is_base_buildable_tile(world, nx, ny, building_type) and not would_block_access(world, nx, ny):
                options += 1
    return options


def _adjacent_special_count(world: World, x: int, y: int) -> int:
    count = 0
    for ix, iy in _important_tiles(world):
        if max(abs(x - ix), abs(y - iy)) <= 1:
            count += 1
    return count


def _important_tiles(world: World) -> list[tuple[int, int]]:
    settlement = world.settlement
    if settlement is None:
        return []

    positions = [(settlement.x, settlement.y)]
    positions.extend((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)
    positions.extend((workshop.x, workshop.y) for workshop in settlement.workshops if workshop.active)
    return positions


def _open_cardinal_neighbors(world: World, x: int, y: int, blocked: set[tuple[int, int]] | None = None) -> int:
    blocked = blocked or set()
    count = 0
    for nx, ny in ((x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)):
        if not _in_bounds(world, nx, ny) or (nx, ny) in blocked:
            continue
        if not world.tile_at(nx, ny).walkable:
            continue
        if world.stockpile_at(nx, ny) is not None or world.workshop_at(nx, ny) is not None:
            continue
        if world.agent_at(nx, ny) is not None:
            continue
        count += 1
    return count


def _in_bounds(world: World, x: int, y: int) -> bool:
    return 0 <= x < world.width and 0 <= y < world.height
