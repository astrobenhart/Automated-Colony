from src.actions import GatherFoodAction
from src.agent import Agent
from src.config import NO_PROGRESS_TICK_LIMIT
from src.roles import BUILDER, SCOUT
from src.tile import Tile
from src.world import World


def make_world(width=5, height=5, kind="grass"):
    world = World(width, height)
    world.tiles = [[Tile(kind) for _ in range(width)] for _ in range(height)]
    return world


def test_critical_thirst_uses_water_plan_over_scout_role():
    world = make_world()
    world.tile_at(4, 2).kind = "water"
    agent = Agent("Scout", 0, 2, thirst=80, role=SCOUT)
    agent.remembered_water.add((4, 2))
    world.colony_memory.remember_water((4, 2))
    world.agents = [agent]

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert action.name == "Seeking water"


def test_critical_hunger_with_carried_food_eats_over_builder_role():
    world = make_world()
    agent = Agent("Builder", 2, 2, hunger=80, food=1, wood=3, role=BUILDER)
    world.agents = [agent]

    action = agent.choose_action(world)

    assert agent.current_goal == "Eat"
    assert action.name == "Eating"


def test_critical_hunger_with_stored_food_eats_from_storage():
    world = make_world()
    world.colony_storage.deposit_food(2)
    agent = Agent("Hungry", 2, 2, hunger=80, food=0)
    world.agents = [agent]

    action = agent.choose_action(world)
    action.execute(agent, world)

    assert agent.current_goal == "Eat from storage"
    assert agent.hunger < 80
    assert world.colony_storage.food == 1


def test_hungry_agent_with_known_food_seeks_food():
    world = make_world()
    world.tile_at(4, 2).food = 2
    agent = Agent("Forager", 0, 2, hunger=80)
    agent.remembered_food.add((4, 2))
    world.agents = [agent]

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather food"
    assert action.name == "Seeking food"


def test_depleted_food_memory_is_cleared_and_ignored():
    world = make_world()
    agent = Agent("Stale", 2, 2, hunger=80)
    stale_target = (4, 2)
    agent.remembered_food.add(stale_target)
    world.colony_memory.remember_food(stale_target)
    agent.current_target = stale_target
    agent.current_path = [(3, 2), stale_target]
    world.agents = [agent]

    action = agent.choose_action(world)

    assert stale_target not in agent.remembered_food
    assert stale_target not in world.colony_memory.known_food
    assert agent.current_target is None
    assert agent.current_path == []
    assert agent.current_goal == "Explore"
    assert action.name == "Wandering"


def test_critical_hunger_without_resource_plan_explores_instead_of_building():
    world = make_world()
    agent = Agent("Builder", 2, 2, hunger=80, wood=3, role=BUILDER)
    world.agents = [agent]

    action = agent.choose_action(world)

    assert agent.current_goal == "Explore"
    assert action.name == "Wandering"


def test_hungry_agent_without_known_resources_moves_when_exploring():
    world = make_world()
    agent = Agent("Lost", 2, 2, hunger=80, thirst=80)
    world.agents = [agent]
    before = (agent.x, agent.y)

    action = agent.choose_action(world)
    action.execute(agent, world)

    assert agent.current_goal == "Explore"
    assert (agent.x, agent.y) != before


def test_no_progress_recovery_clears_stale_path_and_target():
    agent = Agent("Stuck", 0, 0)
    agent.current_target = (4, 4)
    agent.current_path = [(1, 0), (2, 0)]

    for _ in range(NO_PROGRESS_TICK_LIMIT):
        agent.record_no_progress()

    assert agent.current_target is None
    assert agent.current_path == []
    assert agent.current_action == "Recovering"


def test_no_progress_ticks_reset_after_meaningful_progress():
    world = make_world()
    agent = Agent("Gatherer", 2, 2, hunger=40, no_progress_ticks=4)
    world.tile_at(2, 2).food = 1
    world.agents = [agent]
    before = agent.progress_snapshot(world)

    GatherFoodAction().execute(agent, world)
    agent.update_progress_tracking(world, before)

    assert agent.no_progress_ticks == 0
