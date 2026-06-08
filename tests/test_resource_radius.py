from src.actions import SeekFoodAction, SeekWaterAction, SeekWoodAction
from src.agent import Agent
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT
from src.settlement import FOOD, HIGH, LOW, MEDIUM, WATER, WOOD, Settlement, resource_pressure
from src.tile import Tile
from src.world import World


def make_world(width=25, height=12):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement(
        "Willowhold",
        5,
        5,
        1,
        "Spring",
        resource_radius=3,
        expanded_resource_radius=8,
    )
    return world


def test_settlement_has_resource_radius_defaults():
    settlement = Settlement("Willowhold", 5, 5, 1, "Spring")

    assert settlement.resource_radius > 0
    assert settlement.expanded_resource_radius > settlement.resource_radius
    assert settlement.food_pressure == LOW
    assert settlement.wood_pressure == LOW
    assert settlement.water_pressure == LOW


def test_radius_helpers_classify_local_and_far_positions():
    world = make_world()

    assert world.is_within_resource_radius(6, 5)
    assert not world.is_within_resource_radius(12, 5)
    assert world.distance_to_settlement(8, 7) == 3
    assert world.filter_positions_by_settlement_radius({(6, 5), (12, 5)}) == {(6, 5)}


def test_local_food_preferred_over_far_food_under_normal_conditions():
    world = make_world()
    world.colony_storage.deposit_food(10)
    world.tile_at(6, 5).food = 1
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=30, role=GENERALIST)
    world.agents.append(agent)

    target = world.choose_resource_target(agent, FOOD, {(6, 5), (21, 5)})

    assert target == (6, 5)
    assert world.settlement.food_pressure == MEDIUM


def test_far_food_used_when_local_food_is_depleted():
    world = make_world()
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=30, role=GENERALIST)
    world.agents.append(agent)

    target = world.choose_resource_target(agent, FOOD, {(21, 5)})

    assert target == (21, 5)
    assert world.settlement.food_pressure == HIGH


def test_critical_hunger_can_use_far_known_food():
    world = make_world()
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=80, role=FORAGER)
    agent.remembered_food.add((21, 5))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather food"
    assert isinstance(action, SeekFoodAction)


def test_critical_thirst_can_use_far_known_water():
    world = make_world()
    world.tile_at(23, 5).kind = "water"
    agent = Agent("Ari", 20, 5, thirst=80, role=BUILDER)
    agent.remembered_water.add((23, 5))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert isinstance(action, SeekWaterAction)


def test_local_wood_preferred_over_far_wood_under_normal_conditions():
    world = make_world()
    world.colony_storage.deposit_wood(10)
    world.colony_storage.deposit_building_materials(1)
    world.tile_at(5, 5).kind = "shelter"
    world.tile_at(6, 5).kind = "forest"
    world.tile_at(6, 5).wood = 1
    world.tile_at(21, 5).kind = "forest"
    world.tile_at(21, 5).wood = 1
    agent = Agent("Builder", 20, 5, role=BUILDER)
    world.agents.append(agent)

    target = world.choose_resource_target(agent, WOOD, {(6, 5), (21, 5)})

    assert target == (6, 5)


def test_far_wood_used_when_wood_pressure_is_high():
    world = make_world()
    world.tile_at(21, 5).kind = "forest"
    world.tile_at(21, 5).wood = 1
    agent = Agent("Builder", 20, 5, role=BUILDER)
    agent.remembered_wood.add((21, 5))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather wood"
    assert isinstance(action, SeekWoodAction)
    assert world.settlement.wood_pressure == HIGH


def test_scout_has_weaker_local_restriction_than_generalist():
    world = make_world()
    world.colony_storage.deposit_food(10)
    world.tile_at(6, 5).food = 1
    world.tile_at(21, 5).food = 1
    generalist = Agent("General", 20, 5, hunger=30, role=GENERALIST)
    scout = Agent("Scout", 20, 5, hunger=30, role=SCOUT)
    world.agents.append(generalist)

    generalist_target = world.choose_resource_target(generalist, FOOD, {(6, 5), (21, 5)})
    world.agents.remove(generalist)
    world.agents.append(scout)
    scout_target = world.choose_resource_target(scout, FOOD, {(6, 5), (21, 5)})

    assert generalist_target == (6, 5)
    assert scout_target == (21, 5)


def test_forager_prefers_local_food_when_available():
    world = make_world()
    world.colony_storage.deposit_food(10)
    world.tile_at(6, 5).food = 1
    world.tile_at(21, 5).food = 1
    agent = Agent("Forager", 20, 5, hunger=30, role=FORAGER)
    world.agents.append(agent)

    target = world.choose_resource_target(agent, FOOD, {(6, 5), (21, 5)})

    assert target == (6, 5)


def test_builder_prefers_local_wood_when_available():
    world = make_world()
    world.colony_storage.deposit_wood(10)
    world.colony_storage.deposit_building_materials(1)
    world.tile_at(5, 5).kind = "shelter"
    world.tile_at(6, 5).kind = "forest"
    world.tile_at(6, 5).wood = 1
    world.tile_at(21, 5).kind = "forest"
    world.tile_at(21, 5).wood = 1
    agent = Agent("Builder", 20, 5, role=BUILDER)
    world.agents.append(agent)

    target = world.choose_resource_target(agent, WOOD, {(6, 5), (21, 5)})

    assert target == (6, 5)


def test_stale_depleted_local_food_is_ignored():
    world = make_world()
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=80)
    agent.remembered_food.update({(6, 5), (21, 5)})
    world.agents.append(agent)

    SeekFoodAction().execute(agent, world)

    assert (6, 5) not in agent.remembered_food
    assert agent.current_target == (21, 5)


def test_unreachable_near_water_does_not_block_reachable_far_water():
    world = make_world(width=25, height=12)
    for x in range(9, 14):
        for y in range(3, 8):
            world.tile_at(x, y).kind = "mountain"
    world.tile_at(11, 5).kind = "water"
    world.tile_at(23, 5).kind = "water"
    agent = Agent("Ari", 20, 5, thirst=80)
    agent.remembered_water.update({(11, 5), (23, 5)})
    world.agents.append(agent)

    SeekWaterAction().execute(agent, world)

    assert agent.current_target == (23, 5)
    assert agent.current_path


def test_resource_target_scoring_does_not_call_pathfinding(monkeypatch):
    world = make_world()
    world.colony_storage.deposit_food(10)
    world.tile_at(6, 5).food = 1
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=30, role=GENERALIST)
    world.agents.append(agent)

    def fail_find_path(*args, **kwargs):
        raise AssertionError("pathfinding must not run during resource scoring")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    assert world.choose_resource_target(agent, FOOD, {(6, 5), (21, 5)}) == (6, 5)


def test_goal_selection_does_not_pathfind_while_scoring_resource_actions(monkeypatch):
    world = make_world()
    world.tile_at(21, 5).food = 1
    agent = Agent("Ari", 20, 5, hunger=80, role=FORAGER)
    agent.remembered_food.add((21, 5))
    world.agents.append(agent)

    def fail_find_path(*args, **kwargs):
        raise AssertionError("pathfinding must not run during goal/action scoring")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    action = agent.choose_action(world)

    assert isinstance(action, SeekFoodAction)


def test_cached_local_resource_pressure_does_not_rescan_radius_each_call(monkeypatch):
    world = make_world()
    world.colony_storage.deposit_food(10)
    world.tile_at(6, 5).food = 1

    assert resource_pressure(world, FOOD) == MEDIUM

    def fail_tile_at(*args, **kwargs):
        raise AssertionError("cached local resource queries should not rescan tiles")

    monkeypatch.setattr(world, "tile_at", fail_tile_at)

    assert resource_pressure(world, FOOD) == MEDIUM
