from src.agent import Agent
from src.config import COLORS, SETTLEMENT_RADIUS, SYMBOL_LABELS
from src.settlement import nearest_walkable_tile
from src.tile import Tile
from src.world import World, create_world


def make_world(width=8, height=8):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_created_world_has_settlement():
    world = create_world(seed=25)

    assert world.settlement is not None
    assert world.settlement.name
    assert world.settlement.radius == SETTLEMENT_RADIUS


def test_settlement_center_is_walkable_and_not_water_or_mountain():
    world = create_world(seed=26)
    settlement = world.settlement

    tile = world.tile_at(settlement.x, settlement.y)

    assert tile.walkable
    assert tile.kind not in ("water", "mountain")


def test_settlement_center_is_deterministic_for_fixed_seed():
    first = create_world(seed=27)
    second = create_world(seed=27)

    assert (first.settlement.x, first.settlement.y) == (second.settlement.x, second.settlement.y)
    assert first.settlement.name == second.settlement.name


def test_settlement_center_is_near_initial_villager_centroid():
    world = create_world(seed=28)
    settlement = world.settlement
    center_x = round(sum(agent.x for agent in world.agents) / len(world.agents))
    center_y = round(sum(agent.y for agent in world.agents) / len(world.agents))

    distance = abs(settlement.x - center_x) + abs(settlement.y - center_y)

    assert distance <= SETTLEMENT_RADIUS


def test_settlement_population_reflects_living_agents():
    world = make_world()
    world.agents = [
        Agent("Ari", 1, 1),
        Agent("Bryn", 2, 2),
        Agent("Cato", 3, 3, alive=False),
    ]
    world.establish_settlement()
    world.update_settlement_population()

    assert world.settlement.population == 2


def test_nearest_walkable_tile_skips_water_and_mountain():
    world = make_world(width=3, height=3)
    world.tile_at(1, 1).kind = "water"
    world.tile_at(1, 0).kind = "mountain"

    x, y = nearest_walkable_tile(world, 1, 1)

    assert world.tile_at(x, y).walkable


def test_settlement_marker_is_supported_by_config():
    assert "settlement" in COLORS
    assert SYMBOL_LABELS["+"] == "Settlement"
