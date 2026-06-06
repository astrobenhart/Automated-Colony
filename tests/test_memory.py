from src.world import World
from src.tile import Tile
from src.agent import Agent
from src.actions import SeekFoodAction, SeekWaterAction, SeekWoodAction


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
    assert (2, 2) in world.colony_memory.known_food
    assert (10, 5) in world.colony_memory.known_water
    assert (0, 5) in world.colony_memory.known_wood
    assert (0, 0) in world.colony_memory.known_shelters

    # Assertions for out-of-range resources
    assert (11, 5) not in agent.remembered_food
    assert (5, 12) not in agent.remembered_water

    # Test depletion/removal: deplete food at (2, 2)
    world.tiles[2][2].food = 0

    # Scan again
    agent.scan_surroundings(world)

    # Food at (2, 2) should be removed from memory
    assert (2, 2) not in agent.remembered_food
    assert (2, 2) not in world.colony_memory.known_food


def test_colony_memory_shares_water_between_agents():
    world = World(12, 11)
    world.tiles = [[Tile("grass") for _ in range(12)] for _ in range(11)]
    world.tiles[5][10].kind = "water"

    scout = Agent("Scout", 5, 5)
    thirsty_agent = Agent("Thirsty", 0, 5, thirst=80)
    world.agents.extend([scout, thirsty_agent])

    scout.scan_surroundings(world)

    assert (10, 5) in scout.remembered_water
    assert (10, 5) in world.colony_memory.known_water
    assert not thirsty_agent.remembered_water

    action = thirsty_agent.choose_action(world)

    assert thirsty_agent.current_goal == "Drink"
    assert isinstance(action, SeekWaterAction)

    action.execute(thirsty_agent, world)

    assert thirsty_agent.current_action == "Seeking water"
    assert thirsty_agent.current_target == (10, 5)
    assert (thirsty_agent.x, thirsty_agent.y) != (0, 5)


def test_colony_memory_shares_food_between_agents():
    world = World(12, 11)
    world.tiles = [[Tile("grass") for _ in range(12)] for _ in range(11)]
    world.tiles[5][10].food = 2

    scout = Agent("Scout", 5, 5)
    hungry_agent = Agent("Hungry", 0, 5, hunger=80)
    world.agents.extend([scout, hungry_agent])

    scout.scan_surroundings(world)

    assert (10, 5) in scout.remembered_food
    assert (10, 5) in world.colony_memory.known_food
    assert not hungry_agent.remembered_food

    action = hungry_agent.choose_action(world)

    assert hungry_agent.current_goal == "Gather food"
    assert isinstance(action, SeekFoodAction)

    action.execute(hungry_agent, world)

    assert hungry_agent.current_action == "Seeking food"
    assert hungry_agent.current_target == (10, 5)
    assert (hungry_agent.x, hungry_agent.y) != (0, 5)


def test_colony_memory_shares_wood_between_agents():
    world = World(12, 11)
    world.tiles = [[Tile("grass") for _ in range(12)] for _ in range(11)]
    world.tiles[5][10].kind = "forest"
    world.tiles[5][10].wood = 3

    scout = Agent("Scout", 5, 5)
    builder = Agent("Builder", 0, 5)
    world.agents.extend([scout, builder])

    scout.scan_surroundings(world)

    assert (10, 5) in scout.remembered_wood
    assert (10, 5) in world.colony_memory.known_wood
    assert not builder.remembered_wood
    assert world.needs_more_shelters()

    action = builder.choose_action(world)

    assert builder.current_goal == "Gather wood"
    assert isinstance(action, SeekWoodAction)

    action.execute(builder, world)

    assert builder.current_action == "Seeking wood"
    assert builder.current_target == (10, 5)
    assert (builder.x, builder.y) != (0, 5)
