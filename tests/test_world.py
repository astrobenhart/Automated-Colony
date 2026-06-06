from src.agent import Agent
from src.tile import Tile
from src.world import World


def make_world(kinds):
    height = len(kinds)
    width = len(kinds[0])
    world = World(width, height)
    world.tiles = [[Tile(kind) for kind in row] for row in kinds]
    return world


def test_can_move_to_rejects_blocked_terrain_and_occupied_tiles():
    world = make_world([
        ["grass", "water", "mountain"],
        ["grass", "grass", "grass"],
    ])
    world.agents.append(Agent("Ari", 0, 1))

    assert world.can_move_to(0, 0)
    assert not world.can_move_to(1, 0)
    assert not world.can_move_to(2, 0)
    assert not world.can_move_to(0, 1)
    assert not world.can_move_to(-1, 0)
    assert not world.can_move_to(3, 0)


def test_living_agents_excludes_dead_agents():
    world = make_world([["grass", "grass"]])
    alive = Agent("Ari", 0, 0)
    dead = Agent("Bryn", 1, 0, alive=False)
    world.agents.extend([alive, dead])

    assert world.living_agents() == [alive]
