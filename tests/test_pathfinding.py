"""
Tester Agent — automated tests for BFS pathfinding.

All worlds are hand-built (no random generation) so results are deterministic.
"""
from src.world import World
from src.tile import Tile
from src.pathfinding import find_path
from src.agent import Agent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_world(width: int, height: int, kind: str = "grass") -> World:
    """Create a world filled with a single terrain type."""
    world = World(width, height)
    world.tiles = [[Tile(kind) for _ in range(width)] for _ in range(height)]
    return world


# ---------------------------------------------------------------------------
# Basic reachability
# ---------------------------------------------------------------------------

def test_path_same_start_and_destination():
    world = make_world(5, 5)
    path = find_path(world, (0, 0), (0, 0))
    assert path == []


def test_path_adjacent_tiles():
    world = make_world(5, 5)
    path = find_path(world, (0, 0), (1, 0))
    assert path == [(1, 0)]


def test_path_straight_line():
    world = make_world(10, 1)
    path = find_path(world, (0, 0), (4, 0))
    assert len(path) == 4
    assert path[-1] == (4, 0)


def test_path_navigates_around_mountain():
    """
    Layout (5x3):
      . . # . .
      . . # . .
      . . . . .

    # = mountain — path must detour via row 2.
    """
    world = make_world(5, 3)
    world.tiles[0][2].kind = "mountain"  # (x=2, y=0)
    world.tiles[1][2].kind = "mountain"  # (x=2, y=1)

    path = find_path(world, (0, 0), (4, 0))
    assert path  # A path exists.
    # Path must not step through mountains.
    for x, y in path:
        assert world.tile_at(x, y).kind != "mountain"
    assert path[-1] == (4, 0)


def test_path_avoids_water():
    world = make_world(5, 1)
    world.tiles[0][2].kind = "water"  # (x=2, y=0)

    # (0,0) to (4,0) in a single-row map with water at x=2 — unreachable
    # because there is nowhere to go around it.
    path = find_path(world, (0, 0), (4, 0))
    assert path == []


def test_path_unreachable_returns_empty():
    """Completely enclosed destination."""
    world = make_world(5, 5)
    # Surround (2,2) with mountains.
    world.tiles[1][2].kind = "mountain"
    world.tiles[3][2].kind = "mountain"
    world.tiles[2][1].kind = "mountain"
    world.tiles[2][3].kind = "mountain"

    path = find_path(world, (0, 0), (2, 2))
    assert path == []


# ---------------------------------------------------------------------------
# Impassable destination (water tile — agent drinks adjacent)
# ---------------------------------------------------------------------------

def test_path_to_water_tile_stops_adjacent():
    """
    When the destination is a water tile, find_path should redirect to a
    walkable neighbour rather than return an empty path.
    """
    world = make_world(5, 5)
    world.tiles[2][2].kind = "water"  # (x=2, y=2)

    # Start at (0,2) — should reach a tile adjacent to (2,2).
    path = find_path(world, (0, 2), (2, 2))
    assert path  # Path should exist.
    assert path[-1] != (2, 2)  # Should NOT step onto the water tile.
    # The final step should be adjacent to the water tile.
    fx, fy = path[-1]
    wx, wy = 2, 2
    assert max(abs(fx - wx), abs(fy - wy)) == 1


# ---------------------------------------------------------------------------
# Out-of-bounds safety
# ---------------------------------------------------------------------------

def test_path_out_of_bounds_destination_returns_empty():
    world = make_world(5, 5)
    path = find_path(world, (0, 0), (99, 99))
    assert path == []


# ---------------------------------------------------------------------------
# Path validity — every step is walkable
# ---------------------------------------------------------------------------

def test_every_step_is_walkable():
    world = make_world(10, 10)
    # Scatter some obstacles.
    world.tiles[3][5].kind = "mountain"
    world.tiles[4][5].kind = "mountain"
    world.tiles[5][3].kind = "water"

    path = find_path(world, (0, 0), (9, 9))
    for x, y in path:
        assert world.tile_at(x, y).walkable, f"Step ({x},{y}) is not walkable."


def test_path_can_avoid_occupied_tiles():
    world = make_world(5, 3)
    blocker = Agent("Blocker", 2, 1)
    world.agents.append(blocker)

    path = find_path(world, (0, 1), (4, 1), avoid_occupied=True)

    assert path
    assert (2, 1) not in path
    assert path[-1] == (4, 1)


def test_path_returns_empty_when_occupied_destination_is_avoided():
    world = make_world(3, 1)
    blocker = Agent("Blocker", 2, 0)
    world.agents.append(blocker)

    path = find_path(world, (0, 0), (2, 0), avoid_occupied=True)

    assert path == []
