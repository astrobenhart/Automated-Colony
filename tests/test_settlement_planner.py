from src.agent import Agent
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT
from src.settlement import Settlement
from src.settlement_planner import (
    CRISIS_FOOD,
    WORK_SUPPORT,
    WORK_CONSTRUCTION,
    WORK_EXPLORATION,
    WORK_FOOD,
    WORK_WATER,
    WORK_WOOD,
    plan_settlement_work,
    settlement_crisis_state,
    settlement_work_demands,
)
from src.tile import Tile
from src.world import World


def make_world(width=12, height=12):
    world = World(width, height, seed=321)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Plannerhold", width // 2, height // 2, 1, "Spring")
    return world


def test_planner_records_daily_demands_on_settlement():
    world = make_world()
    world.agents.extend(
        [
            Agent("Fenn", 5, 5, role=FORAGER, agent_id="fenn"),
            Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn"),
            Agent("Ira", 6, 5, role=SCOUT, agent_id="ira"),
        ]
    )

    assignments = plan_settlement_work(world)

    assert world.settlement.last_planned_day == world.day
    assert world.settlement.planned_demands[WORK_FOOD] > 0
    assert assignments["ira"] == WORK_EXPLORATION


def test_role_based_assignments_follow_planner_demands():
    world = make_world()
    world.colony_storage.deposit_food(99)
    world.colony_storage.deposit_water(99)
    world.agents.extend(
        [
            Agent("Fenn", 5, 5, role=FORAGER, agent_id="fenn"),
            Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn"),
            Agent("Gala", 6, 5, role=GENERALIST, agent_id="gala"),
            Agent("Ira", 6, 6, role=SCOUT, agent_id="ira"),
        ]
    )

    assignments = plan_settlement_work(world)

    assert assignments["ira"] == WORK_EXPLORATION
    assert assignments["bryn"] in {WORK_WOOD, WORK_CONSTRUCTION}
    assert assignments["fenn"] in {WORK_FOOD, WORK_WATER}
    assert assignments["gala"] in {WORK_FOOD, WORK_WATER, WORK_WOOD, WORK_CONSTRUCTION}


def test_construction_assignment_waits_for_usable_wood():
    world = make_world()
    world.colony_storage.deposit_food(20)
    world.colony_storage.deposit_water(20)
    builder = Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn")
    world.agents.append(builder)

    assignments = plan_settlement_work(world)

    assert world.needs_more_shelters()
    assert assignments["bryn"] == WORK_WOOD

    world.colony_storage.deposit_wood(3)
    assignments = plan_settlement_work(world)

    assert assignments["bryn"] == WORK_CONSTRUCTION


def test_food_crisis_redirects_builders_and_generalists_to_food():
    world = make_world()
    world.colony_storage.deposit_water(20)
    world.tile_at(5, 5).food = 3
    world.settlement.local_food = {(5, 5)}
    builder = Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn")
    generalist = Agent("Gala", 6, 5, role=GENERALIST, agent_id="gala")
    world.agents.extend([builder, generalist])

    assignments = plan_settlement_work(world)

    assert settlement_crisis_state(world) == CRISIS_FOOD
    assert assignments["bryn"] == WORK_FOOD
    assert assignments["gala"] == WORK_FOOD


def test_water_demand_rises_when_water_storage_and_access_are_low():
    world = make_world()
    world.agents.extend(Agent(f"A{i}", 5, 5, role=FORAGER) for i in range(6))
    world.tile_at(1, 1).kind = "shelter"
    world.tile_at(2, 1).kind = "shelter"
    world.colony_storage.deposit_wood(20)
    world.settlement.local_water = set()

    demands = settlement_work_demands(world)

    assert demands[WORK_WATER] > demands[WORK_WOOD]


def test_wood_demand_is_zero_when_reserve_and_construction_are_satisfied():
    world = make_world()
    world.agents.append(Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn"))
    world.agents.append(Agent("Gala", 6, 6, role=GENERALIST, agent_id="gala"))
    world.tile_at(1, 1).kind = "shelter"
    world.colony_storage.deposit_food(99)
    world.colony_storage.deposit_water(99)
    world.colony_storage.deposit_wood(20)
    world.settlement.local_food = {(x, 2) for x in range(6)}
    world.settlement.local_water = {(1, 3), (2, 3)}
    world.settlement.local_wood = {(x, 4) for x in range(6)}

    demands = settlement_work_demands(world)
    assignments = plan_settlement_work(world)

    assert demands[WORK_WOOD] == 0
    assert assignments["bryn"] == WORK_SUPPORT
    assert assignments["gala"] != WORK_WOOD


def test_builder_fallback_supports_food_shortage_before_wood_surplus():
    world = make_world()
    world.agents.append(Agent("Bryn", 5, 6, role=BUILDER, agent_id="bryn"))
    world.tile_at(1, 1).kind = "shelter"
    world.colony_storage.deposit_water(99)
    world.colony_storage.deposit_wood(99)
    world.settlement.local_food = {(5, 5)}
    world.settlement.local_water = {(1, 3), (2, 3)}
    world.settlement.local_wood = {(x, 4) for x in range(6)}

    assignments = plan_settlement_work(world)

    assert assignments["bryn"] == WORK_FOOD
