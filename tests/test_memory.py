from src.world import World
from src.tile import Tile
from src.agent import Agent


def test_agent_memory_scanning():
    # Create a 15x15 world
    world = World(15, 15)
    world.tiles = [[Tile("grass") for _ in range(15)] for _ in range(15)]

    # Place resources within vision range (radius 5 from agent at 5,5)
    # Food at (2, 2) -> Chebyshev distance dx=3, dy=3 -> In range
    world.tiles[2][2].food = 3

    # Water at (10, 5) -> Chebyshev distance dx=5, dy=0 -> In range
    world.tiles[5][10].kind = "water"

    # Forest/wood at (0, 5) -> Chebyshev distance dx=5, dy=0 -> In range
    world.tiles[5][0].kind = "forest"
    world.tiles[5][0].wood = 4

    # Shelter at (0, 0) -> Chebyshev distance dx=5, dy=5 -> In range
    world.tiles[0][0].kind = "shelter"

    # Place resources out of vision range (Chebyshev distance > 5 from agent at 5,5)
    # Food at (11, 5) -> Chebyshev distance dx=6, dy=0 -> Out of range
    world.tiles[5][11].food = 2

    # Water at (5, 12) -> Chebyshev distance dx=0, dy=7 -> Out of range
    world.tiles[12][5].kind = "water"

    # Create agent at (5, 5)
    agent = Agent("TestAgent", 5, 5)
    world.agents.append(agent)

    # Scan surroundings
    agent.scan_surroundings(world)

    # Assertions for remembered resources
    assert (2, 2) in agent.remembered_food
    assert (10, 5) in agent.remembered_water
    assert (0, 5) in agent.remembered_wood
    assert (0, 0) in agent.remembered_shelters

    # Assertions for out-of-range resources
    assert (11, 5) not in agent.remembered_food
    assert (5, 12) not in agent.remembered_water

    # Test depletion/removal: deplete food at (2, 2)
    world.tiles[2][2].food = 0

    # Scan again
    agent.scan_surroundings(world)

    # Food at (2, 2) should be removed from memory
    assert (2, 2) not in agent.remembered_food
