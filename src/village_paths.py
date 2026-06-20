from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.settlement import Settlement
    from src.world import World


PATH = "path"
PATH_BORDER_EDGES = ("north", "south", "west", "east")


def seed_village_paths(world: World, settlement: Settlement):
    """Lay down starter footpaths between core village anchors."""
    from src.pathfinding import find_path

    hub = (settlement.x, settlement.y)
    endpoints = _path_endpoints(world, settlement, hub)

    mark_path_tile(world, settlement, *hub)
    for endpoint in endpoints:
        route = find_path(world, hub, endpoint, avoid_occupied=False)
        if not route and endpoint != hub:
            continue
        for x, y in route:
            mark_path_tile(world, settlement, x, y)


def mark_path_tile(world: World, settlement: Settlement, x: int, y: int) -> bool:
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    if is_reserved_village_structure(settlement, x, y):
        return False

    tile = world.tile_at(x, y)
    if not tile.walkable or tile.kind in ("water", "mountain", "shelter", "home"):
        return False

    tile.kind = PATH
    tile.food = 0
    tile.wood = 0
    return True


def path_border_edges(world: World, x: int, y: int) -> dict[str, bool]:
    return {
        "north": not _is_path_tile(world, x, y - 1),
        "south": not _is_path_tile(world, x, y + 1),
        "west": not _is_path_tile(world, x - 1, y),
        "east": not _is_path_tile(world, x + 1, y),
    }


def _is_path_tile(world: World, x: int, y: int) -> bool:
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    return world.tile_at(x, y).kind == PATH


def _path_endpoints(world: World, settlement: Settlement, hub: tuple[int, int]) -> list[tuple[int, int]]:
    endpoints: list[tuple[int, int]] = []
    blocked = _reserved_village_positions(settlement)

    for home in settlement.homes:
        endpoint = _access_tile(world, home.x, home.y, hub, blocked)
        if endpoint is not None:
            endpoints.append(endpoint)

    for stockpile in settlement.stockpiles:
        endpoint = _access_tile(world, stockpile.x, stockpile.y, hub, blocked)
        if endpoint is not None:
            endpoints.append(endpoint)

    for workshop in settlement.workshops:
        endpoint = _access_tile(world, workshop.x, workshop.y, hub, blocked)
        if endpoint is not None:
            endpoints.append(endpoint)

    endpoints.extend(_water_access_tiles(world, settlement, hub, blocked, limit=2))
    return _unique_positions(endpoints)


def _access_tile(
    world: World,
    x: int,
    y: int,
    hub: tuple[int, int],
    blocked: set[tuple[int, int]],
) -> tuple[int, int] | None:
    candidates = []
    for dy in (0, 1, -1):
        for dx in (0, 1, -1):
            pos = (x + dx, y + dy)
            if pos == (x, y) or pos in blocked:
                continue
            px, py = pos
            if not (0 <= px < world.width and 0 <= py < world.height):
                continue
            if not world.tile_at(px, py).walkable:
                continue
            candidates.append(pos)

    if not candidates:
        return None
    return min(candidates, key=lambda pos: (_distance(pos, hub), pos[1], pos[0]))


def _water_access_tiles(
    world: World,
    settlement: Settlement,
    hub: tuple[int, int],
    blocked: set[tuple[int, int]],
    limit: int,
) -> list[tuple[int, int]]:
    water_tiles = []
    search_radius = max(settlement.resource_radius, settlement.radius)
    for y in range(max(0, settlement.y - search_radius), min(world.height, settlement.y + search_radius + 1)):
        for x in range(max(0, settlement.x - search_radius), min(world.width, settlement.x + search_radius + 1)):
            if max(abs(x - settlement.x), abs(y - settlement.y)) > search_radius:
                continue
            if world.tile_at(x, y).kind != "water":
                continue
            endpoint = _access_tile(world, x, y, hub, blocked)
            if endpoint is not None:
                water_tiles.append((_distance((x, y), hub), endpoint))

    return [endpoint for _, endpoint in sorted(water_tiles, key=lambda item: (item[0], item[1][1], item[1][0]))[:limit]]


def is_reserved_village_structure(settlement: Settlement, x: int, y: int) -> bool:
    return (x, y) in _reserved_village_positions(settlement)


def _reserved_village_positions(settlement: Settlement) -> set[tuple[int, int]]:
    positions = {(home.x, home.y) for home in settlement.homes}
    positions.update((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)
    positions.update((workshop.x, workshop.y) for workshop in settlement.workshops)
    return positions


def _unique_positions(positions: list[tuple[int, int]]) -> list[tuple[int, int]]:
    seen = set()
    unique = []
    for pos in positions:
        if pos in seen:
            continue
        seen.add(pos)
        unique.append(pos)
    return unique


def _distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
