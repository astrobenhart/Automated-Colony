from collections import Counter

from src.config import STARTING_AGENTS
from src.lifecycle import is_valid_lifecycle_stage
from src.roles import is_valid_role
from src.traits import is_valid_trait
from src.world import create_world


def test_starting_village_has_home_count_within_phase_one_range():
    world = create_world(seed=59)

    assert 8 <= len(world.settlement.homes) <= 15


def test_starting_village_has_population_within_phase_one_range():
    world = create_world(seed=60)

    assert 30 <= len(world.agents) <= 60
    assert STARTING_AGENTS == len(world.agents)


def test_starting_homes_are_valid_in_bounds_tiles():
    world = create_world(seed=61)

    home_positions = {(home.x, home.y) for home in world.settlement.homes}
    assert len(home_positions) == len(world.settlement.homes)

    for home in world.settlement.homes:
        assert 0 <= home.x < world.width
        assert 0 <= home.y < world.height
        tile = world.tile_at(home.x, home.y)
        assert tile.kind == "home"
        assert tile.walkable
        assert tile.kind not in ("water", "mountain")
        assert max(abs(home.x - world.settlement.x), abs(home.y - world.settlement.y)) <= world.settlement.radius


def test_starting_homes_keep_minimum_spacing():
    world = create_world(seed=62)
    homes = world.settlement.homes

    for index, home in enumerate(homes):
        for other in homes[index + 1:]:
            assert max(abs(home.x - other.x), abs(home.y - other.y)) >= 3


def test_starting_villagers_spawn_on_valid_home_or_adjacent_tiles():
    world = create_world(seed=63)
    homes = {(home.x, home.y) for home in world.settlement.homes}

    assert homes
    for agent in world.agents:
        assert world.is_valid_spawn_tile(agent.x, agent.y)
        assert any(max(abs(agent.x - hx), abs(agent.y - hy)) <= 1 for hx, hy in homes)
        assert is_valid_role(agent.role)
        assert is_valid_lifecycle_stage(agent.lifecycle_stage)
        assert is_valid_trait(agent.trait)


def test_shared_villager_spawn_tiles_are_allowed():
    world = create_world(seed=64, agent_count=60)
    counts = Counter((agent.x, agent.y) for agent in world.agents)
    shared_tiles = [pos for pos, count in counts.items() if count > 1]

    assert shared_tiles
    for x, y in shared_tiles:
        assert world.can_move_to(x, y)

