from __future__ import annotations

from collections import Counter

from src.building_priorities import DESIRED_WOOD_RESERVE
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT

WORK_FOOD = "food_production"
WORK_WATER = "water_collection"
WORK_WOOD = "wood_gathering"
WORK_CONSTRUCTION = "house_construction"
WORK_EXPLORATION = "exploration"
WORK_SUPPORT = "village_support"

WORK_ASSIGNMENTS = (
    WORK_FOOD,
    WORK_WATER,
    WORK_WOOD,
    WORK_CONSTRUCTION,
    WORK_EXPLORATION,
    WORK_SUPPORT,
)


def plan_settlement_work(world):
    settlement = world.settlement
    if settlement is None:
        return {}

    living = world.living_agents()
    demands = settlement_work_demands(world)
    assignments = {}
    role_counts: Counter[str] = Counter()

    for agent in living:
        assignment = assignment_for_agent(agent, world, demands, role_counts)
        assignments[_agent_key(agent)] = assignment
        role_counts[assignment] += 1
        agent.daily_role = assignment
        if agent.task_state in ("", "idle"):
            agent.task_state = "idle"

    settlement.planned_demands = demands
    settlement.work_assignments = assignments
    settlement.last_planned_day = world.day
    return assignments


def settlement_work_demands(world) -> dict[str, int]:
    population = len(world.living_agents())
    settlement = world.settlement
    local_food = len(settlement.local_food) if settlement is not None else 0
    local_water = len(settlement.local_water) if settlement is not None else 0
    local_wood = len(settlement.local_wood) if settlement is not None else 0

    food_shortage = max(0, population * 2 - world.colony_storage.food)
    water_shortage = max(0, population - world.colony_storage.water)
    wood_shortage = max(0, DESIRED_WOOD_RESERVE - world.colony_storage.wood)

    demands = {
        WORK_FOOD: 20 + food_shortage + max(0, 6 - local_food) * 4,
        WORK_WATER: 10 + water_shortage + max(0, 2 - local_water) * 12,
        WORK_WOOD: 8 + wood_shortage + max(0, 6 - local_wood) * 3,
        WORK_CONSTRUCTION: 0,
        WORK_EXPLORATION: 6,
        WORK_SUPPORT: 1,
    }

    priority = world.building_priority()
    if priority is not None:
        demands[WORK_CONSTRUCTION] = 80 + priority.missing_count * 20
        demands[WORK_WOOD] += priority.wood_needed * 8

    if local_food == 0 or local_water == 0 or local_wood == 0:
        demands[WORK_EXPLORATION] += 30

    return demands


def assignment_for_agent(agent, world, demands: dict[str, int], role_counts: Counter[str]) -> str:
    if agent.role == SCOUT:
        return WORK_EXPLORATION

    if agent.role == BUILDER:
        if demands.get(WORK_CONSTRUCTION, 0) > 0 and _construction_materials_available(world):
            return WORK_CONSTRUCTION
        if demands.get(WORK_WOOD, 0) > 0:
            return WORK_WOOD
        return WORK_SUPPORT

    if agent.role == FORAGER:
        return _balanced_choice(
            (WORK_FOOD, WORK_WATER),
            demands,
            role_counts,
        )

    if agent.role == GENERALIST:
        return _balanced_choice(
            (WORK_FOOD, WORK_WATER, WORK_WOOD, WORK_CONSTRUCTION),
            demands,
            role_counts,
        )

    return WORK_SUPPORT


def assignment_for(world, agent) -> str | None:
    settlement = world.settlement
    if settlement is None:
        return getattr(agent, "daily_role", None)
    return settlement.work_assignments.get(_agent_key(agent), getattr(agent, "daily_role", None))


def _balanced_choice(options: tuple[str, ...], demands: dict[str, int], role_counts: Counter[str]) -> str:
    return max(options, key=lambda work: (demands.get(work, 0) - role_counts[work] * 12, demands.get(work, 0)))


def _construction_materials_available(world) -> bool:
    priority = world.building_priority()
    if priority is None:
        return False
    return world.colony_storage.wood >= priority.wood_cost or world.colony_storage.building_materials > 0


def _agent_key(agent) -> str:
    return agent.agent_id or agent.name
