from src.agent import Agent
from src.actions import (
    BuildShelterAction,
    DrinkAction,
    EatAction,
    GatherFoodAction,
    GatherWoodAction,
    SeekFoodAction,
    SeekWaterAction,
    SleepAction,
    WanderAction,
)
from src.tile import Tile
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_thirst_prioritization():
    world = make_world()
    world.tiles[2][3].kind = "water"
    agent = Agent("TestAgent", 2, 2, hunger=20, thirst=80, fatigue=20)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert isinstance(action, DrinkAction)


def test_thirsty_agent_seeks_remembered_water():
    world = make_world()
    world.tiles[2][4].kind = "water"
    agent = Agent("TestAgent", 0, 2, hunger=1, thirst=80, fatigue=1)
    agent.remembered_water.add((4, 2))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert isinstance(action, SeekWaterAction)

    action.execute(agent, world)

    assert agent.current_action == "Seeking water"
    assert (agent.x, agent.y) != (0, 2)
    assert agent.current_target == (4, 2)


def test_hunger_prioritization():
    world = make_world()
    agent = Agent("TestAgent", 2, 2, hunger=80, thirst=10, fatigue=20, food=1)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Eat"
    assert isinstance(action, EatAction)


def test_hungry_agent_seeks_remembered_food():
    world = make_world()
    world.tiles[2][4].food = 2
    agent = Agent("TestAgent", 0, 2, hunger=80, thirst=1, fatigue=1)
    agent.remembered_food.add((4, 2))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather food"
    assert isinstance(action, SeekFoodAction)

    action.execute(agent, world)

    assert agent.current_action == "Seeking food"
    assert (agent.x, agent.y) == (1, 2)


def test_choose_action_updates_current_goal_from_selected_goal():
    world = make_world()
    agent = Agent("TestAgent", 2, 2, hunger=80, thirst=1, fatigue=1, food=1)
    world.agents.append(agent)

    assert agent.current_goal == "Explore"

    agent.choose_action(world)

    assert agent.current_goal == "Eat"


def test_fatigue_prioritization():
    world = make_world()
    world.tiles[2][2].kind = "shelter"
    agent = Agent("TestAgent", 2, 2, hunger=10, thirst=10, fatigue=80)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Sleep"
    assert isinstance(action, SleepAction)


def test_agent_can_choose_food_gathering():
    world = make_world()
    world.tiles[2][2].food = 2
    agent = Agent("TestAgent", 2, 2, hunger=1, thirst=1, fatigue=1)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather food"
    assert isinstance(action, GatherFoodAction)


def test_agent_can_choose_wood_gathering():
    world = make_world()
    world.tiles[2][2].kind = "forest"
    world.tiles[2][2].wood = 2
    agent = Agent("TestAgent", 2, 2, hunger=1, thirst=1, fatigue=1)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather wood"
    assert isinstance(action, GatherWoodAction)


def test_agent_can_choose_shelter_building():
    world = make_world()
    agent = Agent("TestAgent", 2, 2, hunger=1, thirst=1, fatigue=1, wood=3)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Build shelter"
    assert isinstance(action, BuildShelterAction)


def test_unavailable_survival_goal_does_not_block_building():
    world = make_world()
    agent = Agent("TestAgent", 2, 2, hunger=1, thirst=30, fatigue=1, wood=3)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Build shelter"
    assert isinstance(action, BuildShelterAction)


def test_exploration_fallback():
    world = make_world()
    agent = Agent("TestAgent", 2, 2, hunger=1, thirst=1, fatigue=1)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Explore"
    assert isinstance(action, WanderAction)
