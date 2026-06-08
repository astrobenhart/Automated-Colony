from collections import Counter

from src.agent import Agent
from src.actions import GatherFoodAction, GatherWoodAction, SeekWaterAction, SleepAction, WanderAction
from src.roles import BUILDER, FORAGER, GENERALIST, ROLES, SCOUT, is_valid_role, role_for_index
from src.tile import Tile
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_roles_are_valid_and_assigned_by_weighted_cycle():
    roles = [role_for_index(index) for index in range(20)]

    assert all(is_valid_role(role) for role in roles)
    assert set(ROLES) == {GENERALIST, FORAGER, BUILDER, SCOUT}
    assert Counter(roles) == {
        GENERALIST: 8,
        FORAGER: 5,
        BUILDER: 5,
        SCOUT: 2,
    }


def test_spawned_agents_receive_roles():
    world = make_world(width=20, height=20)
    world.spawn_agents(20)

    assert all(is_valid_role(agent.role) for agent in world.agents)
    assert Counter(agent.role for agent in world.agents) == {
        GENERALIST: 8,
        FORAGER: 5,
        BUILDER: 5,
        SCOUT: 2,
    }


def test_builder_role_biases_routine_choice_toward_wood():
    world = make_world()
    world.tiles[2][2].kind = "forest"
    world.tiles[2][2].food = 1
    world.tiles[2][2].wood = 1

    generalist = Agent("Ari", 2, 2, role=GENERALIST)
    builder = Agent("Bryn", 2, 2, role=BUILDER)

    world.agents.append(generalist)
    generalist_action = generalist.choose_action(world)
    world.agents.remove(generalist)

    world.agents.append(builder)
    builder_action = builder.choose_action(world)

    assert isinstance(generalist_action, GatherFoodAction)
    assert isinstance(builder_action, GatherWoodAction)
    assert builder.current_goal == "Gather wood"


def test_scout_role_biases_routine_choice_toward_exploration():
    world = make_world()
    world.tiles[2][2].food = 1
    scout = Agent("Cato", 2, 2, role=SCOUT)
    world.agents.append(scout)

    action = scout.choose_action(world)

    assert scout.current_goal == "Explore"
    assert isinstance(action, WanderAction)


def test_urgent_thirst_overrides_scout_preference():
    world = make_world()
    world.tiles[2][4].kind = "water"
    scout = Agent("Dara", 0, 2, thirst=80, role=SCOUT)
    scout.remembered_water.add((4, 2))
    world.agents.append(scout)

    action = scout.choose_action(world)

    assert scout.current_goal == "Drink"
    assert isinstance(action, SeekWaterAction)


def test_urgent_hunger_overrides_builder_preference():
    world = make_world()
    world.tiles[2][2].kind = "forest"
    world.tiles[2][2].food = 1
    world.tiles[2][2].wood = 1
    builder = Agent("Eli", 2, 2, hunger=80, role=BUILDER)
    world.agents.append(builder)

    action = builder.choose_action(world)

    assert builder.current_goal == "Gather food"
    assert isinstance(action, GatherFoodAction)


def test_urgent_fatigue_overrides_forager_preference():
    world = make_world()
    world.tiles[2][2].kind = "shelter"
    world.tiles[2][2].food = 1
    forager = Agent("Fenn", 2, 2, fatigue=80, role=FORAGER)
    world.agents.append(forager)

    action = forager.choose_action(world)

    assert forager.current_goal == "Sleep"
    assert isinstance(action, SleepAction)
