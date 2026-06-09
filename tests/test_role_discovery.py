from src.agent import Agent
from src.roles import BUILDER, FOOD, FORAGER, GENERALIST, SCOUT, WATER, WOOD, discovery_radius
from src.tile import Tile
from src.world import World


def make_world(width: int = 17, height: int = 17) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_discovery_radius_table_matches_first_pass_values():
    assert discovery_radius(SCOUT, FOOD) == 6
    assert discovery_radius(SCOUT, WOOD) == 6
    assert discovery_radius(SCOUT, WATER) == 6

    assert discovery_radius(FORAGER, FOOD) == 5
    assert discovery_radius(FORAGER, WOOD) == 4
    assert discovery_radius(FORAGER, WATER) == 5

    assert discovery_radius(GENERALIST, FOOD) == 4
    assert discovery_radius(GENERALIST, WOOD) == 4
    assert discovery_radius(GENERALIST, WATER) == 4

    assert discovery_radius(BUILDER, FOOD) == 2
    assert discovery_radius(BUILDER, WOOD) == 3
    assert discovery_radius(BUILDER, WATER) == 2


def test_scout_discovers_food_farther_than_generalist():
    world = make_world()
    world.tiles[8][14].food = 1
    scout = Agent("Scout", 8, 8, role=SCOUT)
    generalist = Agent("Generalist", 8, 8, role=GENERALIST)

    generalist.scan_surroundings(world)
    assert (14, 8) not in generalist.remembered_food
    assert (14, 8) not in world.colony_memory.known_food

    scout.scan_surroundings(world)
    assert (14, 8) in scout.remembered_food
    assert (14, 8) in world.colony_memory.known_food


def test_scout_discovers_water_farther_than_builder():
    world = make_world()
    world.tiles[8][14].kind = "water"
    builder = Agent("Builder", 8, 8, role=BUILDER)
    scout = Agent("Scout", 8, 8, role=SCOUT)

    builder.scan_surroundings(world)
    assert (14, 8) not in builder.remembered_water

    scout.scan_surroundings(world)
    assert (14, 8) in scout.remembered_water
    assert (14, 8) in world.colony_memory.known_water


def test_forager_discovers_food_farther_than_builder():
    world = make_world()
    world.tiles[8][13].food = 1
    builder = Agent("Builder", 8, 8, role=BUILDER)
    forager = Agent("Forager", 8, 8, role=FORAGER)

    builder.scan_surroundings(world)
    assert (13, 8) not in builder.remembered_food

    forager.scan_surroundings(world)
    assert (13, 8) in forager.remembered_food
    assert (13, 8) in world.colony_memory.known_food


def test_builder_wood_discovery_differs_from_builder_food_discovery():
    world = make_world()
    world.tiles[8][11].food = 1
    world.tiles[11][8].kind = "forest"
    world.tiles[11][8].wood = 1
    builder = Agent("Builder", 8, 8, role=BUILDER)

    builder.scan_surroundings(world)

    assert (11, 8) not in builder.remembered_food
    assert (8, 11) in builder.remembered_wood
    assert (8, 11) in world.colony_memory.known_wood


def test_resources_outside_discovery_radius_are_not_discovered():
    world = make_world(width=18, height=18)
    world.tiles[8][15].food = 1
    scout = Agent("Scout", 8, 8, role=SCOUT)

    scout.scan_surroundings(world)

    assert (15, 8) not in scout.remembered_food
    assert (15, 8) not in world.colony_memory.known_food


def test_resources_inside_discovery_radius_are_discovered():
    world = make_world()
    world.tiles[8][12].food = 1
    generalist = Agent("Generalist", 8, 8, role=GENERALIST)

    generalist.scan_surroundings(world)

    assert (12, 8) in generalist.remembered_food
    assert (12, 8) in world.colony_memory.known_food


def test_forgetting_behavior_still_removes_depleted_known_resources():
    world = make_world()
    world.tiles[8][12].food = 1
    generalist = Agent("Generalist", 8, 8, role=GENERALIST)
    generalist.scan_surroundings(world)
    assert (12, 8) in world.colony_memory.known_food

    world.tiles[8][12].food = 0
    generalist.scan_surroundings(world)

    assert (12, 8) not in generalist.remembered_food
    assert (12, 8) not in world.colony_memory.known_food


def test_unknown_roles_use_safe_generalist_fallback_radius():
    world = make_world()
    world.tiles[8][12].food = 1
    world.tiles[8][13].kind = "forest"
    world.tiles[8][13].wood = 1
    unknown = Agent("Mystery", 8, 8, role="Mystery")

    unknown.scan_surroundings(world)

    assert unknown.discovery_radius(FOOD) == discovery_radius(GENERALIST, FOOD)
    assert (12, 8) in unknown.remembered_food
    assert (13, 8) not in unknown.remembered_wood
