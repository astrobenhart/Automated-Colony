from __future__ import annotations
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.world import World


def find_path(
    world: World,
    start: tuple[int, int],
    destination: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    BFS pathfinding from start to destination.

    Returns an ordered list of (x, y) tiles to walk through, excluding start
    and including destination. Returns an empty list if:
    - start == destination
    - destination is unreachable

    Paths avoid water and mountain tiles unless the destination itself is
    impassable (e.g. a water tile), in which case the path leads to the
    nearest walkable tile adjacent to the destination.
    """
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
        destination = _nearest_walkable_neighbor(world, destination)
        if destination is None or destination == start:
            return []

    queue: deque[tuple[int, int]] = deque()
    queue.append(start)
    # Maps each visited coord to the coord it came from.
    visited: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while queue:
        current = queue.popleft()

        if current == destination:
            return _reconstruct_path(visited, start, destination)

        cx, cy = current
        for ddx, ddy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cx + ddx, cy + ddy
            neighbor = (nx, ny)

            if neighbor in visited:
                continue
            if not (0 <= nx < world.width and 0 <= ny < world.height):
                continue
            if not world.tile_at(nx, ny).walkable:
                continue

            visited[neighbor] = current
            queue.append(neighbor)

    return []  # Destination unreachable.


def _nearest_walkable_neighbor(
    world: World,
    pos: tuple[int, int],
) -> tuple[int, int] | None:
    """Return the first walkable cardinal neighbour of pos, or None."""
    px, py = pos
    for ddx, ddy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx, ny = px + ddx, py + ddy
        if 0 <= nx < world.width and 0 <= ny < world.height:
            if world.tile_at(nx, ny).walkable:
                return (nx, ny)
    return None


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
