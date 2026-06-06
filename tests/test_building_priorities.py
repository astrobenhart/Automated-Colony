from src.agent import Agent
from src.building_priorities import SHELTER, highest_priority
from src.tile import Tile
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def add_shelters(world: World, positions: list[tuple[int, int]]):
    for x, y in positions:
        world.tiles[y][x].kind = "shelter"


def test_colony_needs_shelter_when_below_capacity():
    world = make_world()
    world.agents.extend([
        Agent("Ari", 0, 0),
        Agent("Bryn", 1, 0),
        Agent("Cato", 2, 0),
        Agent("Dara", 3, 0),
    ])

    priority = highest_priority(world)

    assert world.needed_shelters() == 2
    assert world.needs_more_shelters()
    assert world.highest_building_priority() == SHELTER
    assert priority is not None
    assert priority.building_type == SHELTER
    assert priority.existing_count == 0
    assert priority.needed_count == 2
    assert priority.missing_count == 2
    assert priority.wood_needed == 6


def test_colony_does_not_need_shelter_when_capacity_met():
    world = make_world()
    world.agents.extend([
        Agent("Ari", 0, 0),
        Agent("Bryn", 1, 0),
        Agent("Cato", 2, 0),
    ])
    add_shelters(world, [(0, 1)])

    assert world.needed_shelters() == 1
    assert not world.needs_more_shelters()
    assert world.highest_building_priority() is None
    assert highest_priority(world) is None


def test_should_gather_wood_only_when_construction_needs_wood():
    world = make_world()
    agent = Agent("Ari", 0, 0)
    world.agents.append(agent)

    assert world.should_gather_wood_for_construction(agent)

    agent.wood = 3

    assert not world.should_gather_wood_for_construction(agent)


def test_no_building_priority_when_no_living_agents():
    world = make_world()
    world.agents.append(Agent("Ari", 0, 0, alive=False))

    assert world.needed_shelters() == 0
    assert not world.needs_more_shelters()
    assert world.highest_building_priority() is None
