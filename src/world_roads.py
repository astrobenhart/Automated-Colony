from __future__ import annotations

import random
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import TYPE_CHECKING

from src.pathfinding import movement_cost
from src.village_paths import ROAD_ORIGIN_WORLD, mark_path_tile

if TYPE_CHECKING:
    from src.settlement import Settlement
    from src.world import World


MAIN_ROAD_COUNT_MIN = 2
MAIN_ROAD_COUNT_MAX = 3


@dataclass(frozen=True)
class MainRoad:
    road_id: str
    edge: str
    path: list[tuple[int, int]]

    @property
    def village_anchor(self) -> tuple[int, int]:
        return self.path[0]

    @property
    def edge_anchor(self) -> tuple[int, int]:
        return self.path[-1]


def seed_main_roads(world: World, settlement: Settlement) -> list[MainRoad]:
    """Seed deterministic roads from the village to world-edge entry points."""
    rng = random.Random(f"{world.seed}|{settlement.settlement_id}|main-roads")
    edges = _selected_edges(world, settlement, rng)
    roads: list[MainRoad] = []
    hub = (settlement.x, settlement.y)

    for edge in edges:
        route = _route_to_edge(world, hub, edge, rng)
        if not route:
            continue
        full_path = [hub] + route
        for x, y in full_path:
            mark_path_tile(world, settlement, x, y, road_origin=ROAD_ORIGIN_WORLD, allow_bridge=True)
        roads.append(MainRoad(road_id=f"road-{len(roads)}", edge=edge, path=full_path))

    world.main_roads = roads
    return roads


def _selected_edges(world: World, settlement: Settlement, rng: random.Random) -> list[str]:
    edges = ["north", "south", "west", "east"]
    edges.sort(key=lambda edge: (_edge_distance(world, settlement, edge), rng.random()))
    count = min(MAIN_ROAD_COUNT_MAX, max(MAIN_ROAD_COUNT_MIN, len(edges) - 1))
    chosen = edges[:count]
    rng.shuffle(chosen)
    return chosen


def _edge_distance(world: World, settlement: Settlement, edge: str) -> int:
    if edge == "north":
        return settlement.y
    if edge == "south":
        return world.height - 1 - settlement.y
    if edge == "west":
        return settlement.x
    return world.width - 1 - settlement.x


def _route_to_edge(world: World, hub: tuple[int, int], edge: str, rng: random.Random) -> list[tuple[int, int]]:
    candidates = _edge_candidates(world, hub, edge, rng)
    for target in candidates:
        route = _find_world_road_route(world, hub, target)
        if route and route[-1] == target:
            return route
    return []


def _find_world_road_route(
    world: World,
    start: tuple[int, int],
    destination: tuple[int, int],
) -> list[tuple[int, int]]:
    """Route permanent roads while allowing expensive bridge crossings over water."""
    if start == destination:
        return []
    if not (0 <= destination[0] < world.width and 0 <= destination[1] < world.height):
        return []

    frontier: list[tuple[int, int, int, tuple[int, int]]] = []
    heappush(frontier, (0, start[1], start[0], start))
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    costs: dict[tuple[int, int], int] = {start: 0}

    while frontier:
        current_cost, _, _, current = heappop(frontier)
        if current_cost != costs[current]:
            continue
        if current == destination:
            return _reconstruct_path(came_from, start, destination)

        cx, cy = current
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nx = cx + dx
            ny = cy + dy
            if not (0 <= nx < world.width and 0 <= ny < world.height):
                continue
            tile = world.tile_at(nx, ny)
            if tile.kind == "mountain":
                continue
            if tile.kind in ("home", "shelter"):
                continue

            step_cost = _world_road_step_cost(tile.kind)
            new_cost = current_cost + step_cost
            neighbor = (nx, ny)
            if neighbor in costs and new_cost >= costs[neighbor]:
                continue

            costs[neighbor] = new_cost
            came_from[neighbor] = current
            heappush(frontier, (new_cost, ny, nx, neighbor))

    return []


def _world_road_step_cost(kind: str) -> int:
    if kind == "water":
        return 38
    return movement_cost(kind)


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int] | None],
    start: tuple[int, int],
    destination: tuple[int, int],
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    current = destination
    while current != start:
        path.append(current)
        parent = came_from[current]
        assert parent is not None
        current = parent
    path.reverse()
    return path


def _edge_candidates(
    world: World,
    hub: tuple[int, int],
    edge: str,
    rng: random.Random,
) -> list[tuple[int, int]]:
    if edge in {"north", "south"}:
        y = 0 if edge == "north" else world.height - 1
        positions = [(x, y) for x in range(world.width)]
    else:
        x = 0 if edge == "west" else world.width - 1
        positions = [(x, y) for y in range(world.height)]

    passable = [pos for pos in positions if world.tile_at(pos[0], pos[1]).kind != "mountain"]
    passable.sort(key=lambda pos: (abs(pos[0] - hub[0]) + abs(pos[1] - hub[1]), rng.random()))
    return passable
