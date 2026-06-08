from src.config import INITIAL_SPAWN_MAX_RADIUS, STARTING_AGENTS
from src.roles import role_for_index
from src.settlement import Settlement, Stockpile, FOOD, WOOD, distance_to_settlement
from src.tile import Tile
from src.workshop import Workshop
from src.world import World, create_world


def make_world(width=15, height=15):
    world = World(width, height, seed=123)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_villagers_spawn_near_settlement_center_on_valid_tiles():
    world = create_world(seed=33)

    assert len(world.agents) == STARTING_AGENTS
    for agent in world.agents:
        assert distance_to_settlement(world, agent.x, agent.y) <= INITIAL_SPAWN_MAX_RADIUS
        tile = world.tile_at(agent.x, agent.y)
        assert tile.walkable
        assert tile.kind not in ("water", "mountain")


def test_villager_spawn_positions_are_unique_and_in_bounds():
    world = create_world(seed=34)
    positions = {(agent.x, agent.y) for agent in world.agents}

    assert len(positions) == len(world.agents)
    for x, y in positions:
        assert 0 <= x < world.width
        assert 0 <= y < world.height


def test_villagers_do_not_spawn_on_water_mountains_or_special_tiles():
    world = create_world(seed=35)
    settlement = world.settlement
    special = {(settlement.x, settlement.y)}
    special.update((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)
    special.update((workshop.x, workshop.y) for workshop in settlement.workshops)

    for agent in world.agents:
        tile = world.tile_at(agent.x, agent.y)
        assert tile.walkable
        assert tile.kind not in ("water", "mountain")
        assert (agent.x, agent.y) not in special


def test_spawn_expands_safely_when_local_area_is_blocked():
    world = make_world(width=15, height=15)
    world.settlement = Settlement("Willowhold", 7, 7, 1, "Spring")
    for y in range(world.height):
        for x in range(world.width):
            if (x, y) != (7, 7):
                world.tile_at(x, y).kind = "mountain"
    open_positions = [(2, 7), (12, 7), (7, 2), (7, 12)]
    for x, y in open_positions:
        world.tile_at(x, y).kind = "grass"

    positions = world.initial_spawn_positions(4)

    assert len(positions) == 4
    assert set(positions) == set(open_positions)


def test_startup_is_deterministic_for_fixed_seed():
    first = create_world(seed=36)
    second = create_world(seed=36)

    assert (first.settlement.x, first.settlement.y) == (second.settlement.x, second.settlement.y)
    assert [(agent.name, agent.role, agent.x, agent.y) for agent in first.agents] == [
        (agent.name, agent.role, agent.x, agent.y) for agent in second.agents
    ]


def test_role_assignment_order_is_preserved_at_startup():
    world = create_world(seed=37, agent_count=6)

    assert [agent.role for agent in world.agents] == [role_for_index(index) for index in range(6)]


def test_settlement_population_matches_spawned_living_villagers():
    world = create_world(seed=38)

    assert world.settlement.population == len(world.living_agents())


def test_stockpiles_and_workshop_initialize_before_spawn_exclusions():
    world = create_world(seed=39)
    settlement = world.settlement
    occupied = {(agent.x, agent.y) for agent in world.agents}

    assert {stockpile.stockpile_type for stockpile in settlement.stockpiles} == {FOOD, WOOD}
    assert settlement.workshops
    assert all((stockpile.x, stockpile.y) not in occupied for stockpile in settlement.stockpiles)
    assert all((workshop.x, workshop.y) not in occupied for workshop in settlement.workshops)


def test_spawn_avoids_preexisting_stockpile_and_workshop_tiles():
    world = make_world(width=9, height=9)
    world.settlement = Settlement(
        "Willowhold",
        4,
        4,
        1,
        "Spring",
        stockpiles=[Stockpile(4, 5, FOOD), Stockpile(5, 4, WOOD)],
        workshops=[Workshop(3, 4)],
    )

    positions = world.initial_spawn_positions(5)

    assert (4, 4) not in positions
    assert (4, 5) not in positions
    assert (5, 4) not in positions
    assert (3, 4) not in positions
