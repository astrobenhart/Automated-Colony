from __future__ import annotations
from heapq import heappop, heappush
from typing import TYPE_CHECKING

from src.profiler import profiler
from src.village_paths import PATH

if TYPE_CHECKING:
    from src.world import World


def find_path(
    world: World,
    start: tuple[int, int],
    destination: tuple[int, int],
    avoid_occupied: bool = False,
) -> list[tuple[int, int]]:
    """
    Weighted pathfinding from start to destination.

    Returns an ordered list of (x, y) tiles to walk through, excluding start
    and including destination. Returns an empty list if:
    - start == destination
    - destination is unreachable

    Paths avoid water and mountain tiles unless the destination itself is
    impassable (e.g. a water tile), in which case the path leads to a
    walkable tile adjacent to the destination.

    If avoid_occupied is True, paths avoid occupied tiles except the start
    tile occupied by the moving agent.
    """
    if hasattr(world, "pathfinding_calls"):
        world.pathfinding_calls += 1
    with profiler.time("pathfinding"):
        return _find_path(world, start, destination, avoid_occupied)


def _find_path(
    world: World,
    start: tuple[int, int],
    destination: tuple[int, int],
    avoid_occupied: bool = False,
) -> list[tuple[int, int]]:
    if start == destination:
        return []

    # Reject out-of-bounds destinations immediately.
    dx_map, dy_map = destination
    if not (0 <= dx_map < world.width and 0 <= dy_map < world.height):
        return []

    # If the destination itself is not walkable (e.g. a water tile the agent
    # wants to drink from), retarget to the closest walkable neighbour.
    dest_tile = world.tile_at(dx_map, dy_map)
    if not dest_tile.walkable:
        destination = _nearest_walkable_neighbor(world, start, destination, avoid_occupied)
        if destination is None or destination == start:
            return []
    elif avoid_occupied and destination != start and world.agent_at(*destination) is not None:
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
        for ddx, ddy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cx + ddx, cy + ddy
            neighbor = (nx, ny)

            if not (0 <= nx < world.width and 0 <= ny < world.height):
                continue
            tile = world.tile_at(nx, ny)
            if not tile.walkable:
                continue
            if avoid_occupied and neighbor != start and world.agent_at(nx, ny) is not None:
                continue

            new_cost = current_cost + movement_cost(tile.kind)
            if neighbor in costs and new_cost >= costs[neighbor]:
                continue

            costs[neighbor] = new_cost
            came_from[neighbor] = current
            heappush(frontier, (new_cost, ny, nx, neighbor))

    return []  # Destination unreachable.


def movement_cost(kind: str) -> int:
    costs = {
        PATH: 4,
        "grass": 10,
        "home": 10,
        "shelter": 10,
        "plain": 11,
        "dry": 13,
        "forest": 14,
        "hill": 16,
        "wetland": 18,
    }
    return costs.get(kind, 12)


def _nearest_walkable_neighbor(
    world: World,
    start: tuple[int, int],
    pos: tuple[int, int],
    avoid_occupied: bool = False,
) -> tuple[int, int] | None:
    """Return the first walkable cardinal neighbour of pos, or None."""
    px, py = pos
    candidates: list[tuple[int, int]] = []

    for ddx, ddy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx, ny = px + ddx, py + ddy
        if 0 <= nx < world.width and 0 <= ny < world.height:
            if world.tile_at(nx, ny).walkable:
                neighbor = (nx, ny)
                if avoid_occupied and neighbor != start and world.agent_at(nx, ny) is not None:
                    continue
                candidates.append(neighbor)

    if not candidates:
        return None

    return min(candidates, key=lambda candidate: abs(candidate[0] - start[0]) + abs(candidate[1] - start[1]))


def _reconstruct_path(
    visited: dict[tuple[int, int], tuple[int, int] | None],
    start: tuple[int, int],
    destination: tuple[int, int],
) -> list[tuple[int, int]]:
    """Walk the visited map backwards to reconstruct the ordered path."""
    path: list[tuple[int, int]] = []
    current: tuple[int, int] = destination
    while current != start:
        path.append(current)
        parent = visited[current]
        assert parent is not None
        current = parent
    path.reverse()
    return path
