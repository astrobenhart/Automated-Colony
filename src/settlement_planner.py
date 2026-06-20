from __future__ import annotations

from collections import Counter

from src.building_priorities import DESIRED_WOOD_RESERVE
from src.config import (
    SETTLEMENT_FOOD_CRISIS_DAYS,
    SETTLEMENT_FOOD_TARGET_DAYS,
    SETTLEMENT_WATER_CRISIS_DAYS,
    SETTLEMENT_WATER_TARGET_DAYS,
)
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT

WORK_FOOD = "food_production"
WORK_WATER = "water_collection"
WORK_WOOD = "wood_gathering"
WORK_CONSTRUCTION = "house_construction"
WORK_EXPLORATION = "exploration"
WORK_SUPPORT = "village_support"
CRISIS_FOOD = "Food Crisis"
CRISIS_WATER = "Water Crisis"
BASE_FOOD_DEMAND = 20
BASE_WATER_DEMAND = 10
BASE_EXPLORATION_DEMAND = 6
BASE_SUPPORT_DEMAND = 1

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

    food_target = population * SETTLEMENT_FOOD_TARGET_DAYS
    water_target = population * SETTLEMENT_WATER_TARGET_DAYS
    food_shortage = max(0, food_target - world.colony_storage.food)
    water_shortage = max(0, water_target - world.colony_storage.water)
    wood_reserve_shortage = max(0, DESIRED_WOOD_RESERVE - world.colony_storage.wood)

    demands = {
        WORK_FOOD: BASE_FOOD_DEMAND + food_shortage * 2 + max(0, 6 - local_food) * 5,
        WORK_WATER: BASE_WATER_DEMAND + water_shortage * 2 + max(0, 2 - local_water) * 14,
        WORK_WOOD: wood_reserve_shortage * 4,
        WORK_CONSTRUCTION: 0,
        WORK_EXPLORATION: BASE_EXPLORATION_DEMAND,
        WORK_SUPPORT: BASE_SUPPORT_DEMAND,
    }

    priority = world.building_priority()
    if priority is not None:
        demands[WORK_CONSTRUCTION] = 80 + priority.missing_count * 20
        available_wood = world.colony_storage.wood + world.colony_storage.building_materials
        construction_wood_shortage = max(0, priority.wood_needed - available_wood)
        demands[WORK_WOOD] += construction_wood_shortage * 8

    crisis = settlement_crisis_state(world)
    if crisis == CRISIS_FOOD:
        demands[WORK_FOOD] += population * 6
        demands[WORK_CONSTRUCTION] = 0
        demands[WORK_WOOD] = min(demands[WORK_WOOD], 12)
        demands[WORK_EXPLORATION] = 2 if local_food > 0 else demands[WORK_EXPLORATION] + 25
    elif crisis == CRISIS_WATER:
        demands[WORK_WATER] += population * 6
        demands[WORK_CONSTRUCTION] = 0
        demands[WORK_WOOD] = min(demands[WORK_WOOD], 12)
        demands[WORK_EXPLORATION] = 2 if local_water > 0 else demands[WORK_EXPLORATION] + 25

    if local_food == 0 or local_water == 0 or local_wood == 0:
        demands[WORK_EXPLORATION] += 30

    return demands


def assignment_for_agent(agent, world, demands: dict[str, int], role_counts: Counter[str]) -> str:
    crisis_assignment = crisis_assignment_for_agent(agent, world)
    if crisis_assignment is not None:
        return crisis_assignment

    if agent.role == SCOUT:
        return WORK_EXPLORATION

    if agent.role == BUILDER:
        if demands.get(WORK_CONSTRUCTION, 0) > 0 and _construction_materials_available(world, agent):
            return WORK_CONSTRUCTION
        if demands.get(WORK_WOOD, 0) > 0:
            return WORK_WOOD
        return _builder_fallback_assignment(demands)

    if agent.role == FORAGER:
        return _balanced_choice(
            (WORK_FOOD, WORK_WATER),
            demands,
            role_counts,
        )

    if agent.role == GENERALIST:
        options = [WORK_FOOD, WORK_WATER]
        if demands.get(WORK_WOOD, 0) > 0:
            options.append(WORK_WOOD)
        if demands.get(WORK_CONSTRUCTION, 0) > 0 and _construction_materials_available(world, agent):
            options.append(WORK_CONSTRUCTION)
        return _balanced_choice(tuple(options), demands, role_counts)

    return WORK_SUPPORT


def assignment_for(world, agent) -> str | None:
    settlement = world.settlement
    if settlement is None:
        return getattr(agent, "daily_role", None)
    crisis_assignment = crisis_assignment_for_agent(agent, world)
    if crisis_assignment is not None:
        return crisis_assignment
    return settlement.work_assignments.get(_agent_key(agent), getattr(agent, "daily_role", None))


def settlement_crisis_state(world) -> str | None:
    food_crisis, water_crisis = survival_crisis_flags(world)
    if not food_crisis and not water_crisis:
        return None

    settlement = world.settlement
    local_food = len(settlement.local_food) if settlement is not None else 0
    local_water = len(settlement.local_water) if settlement is not None else 0
    if food_crisis and (not water_crisis or local_food <= local_water):
        return CRISIS_FOOD
    if water_crisis:
        return CRISIS_WATER
    return None


def crisis_assignment_for_agent(agent, world) -> str | None:
    food_crisis, water_crisis = survival_crisis_flags(world)
    if not food_crisis and not water_crisis:
        return None

    settlement = world.settlement
    local_food = len(settlement.local_food) if settlement is not None else 0
    local_water = len(settlement.local_water) if settlement is not None else 0

    if food_crisis and water_crisis:
        if agent.role == SCOUT and local_food == 0 and local_water == 0:
            return WORK_EXPLORATION
        return WORK_WATER if _stable_agent_index(agent) % 2 == 0 else WORK_FOOD
    if food_crisis:
        if agent.role == SCOUT and local_food == 0:
            return WORK_EXPLORATION
        return WORK_FOOD
    if water_crisis:
        if agent.role == SCOUT and local_water == 0:
            return WORK_EXPLORATION
        return WORK_WATER
    return None


def survival_crisis_flags(world) -> tuple[bool, bool]:
    population = len(world.living_agents())
    if population <= 0:
        return False, False

    food_crisis = world.colony_storage.food <= population * SETTLEMENT_FOOD_CRISIS_DAYS
    water_crisis = world.colony_storage.water <= population * SETTLEMENT_WATER_CRISIS_DAYS
    return food_crisis, water_crisis


def _stable_agent_index(agent) -> int:
    key = _agent_key(agent)
    digits = "".join(char for char in key if char.isdigit())
    if digits:
        return int(digits)
    return sum(ord(char) for char in key)


def _balanced_choice(options: tuple[str, ...], demands: dict[str, int], role_counts: Counter[str]) -> str:
    return max(options, key=lambda work: (demands.get(work, 0) - role_counts[work] * 12, demands.get(work, 0)))


def _builder_fallback_assignment(demands: dict[str, int]) -> str:
    options = []
    if demands.get(WORK_FOOD, 0) > BASE_FOOD_DEMAND:
        options.append(WORK_FOOD)
    if demands.get(WORK_WATER, 0) > BASE_WATER_DEMAND:
        options.append(WORK_WATER)
    if demands.get(WORK_CONSTRUCTION, 0) > 0:
        options.append(WORK_CONSTRUCTION)
    if demands.get(WORK_WOOD, 0) > 0:
        options.append(WORK_WOOD)

    if not options:
        return WORK_SUPPORT
    return max(options, key=lambda work: demands.get(work, 0))


def _construction_materials_available(world, agent=None) -> bool:
    priority = world.building_priority()
    if priority is None:
        return False
    carried_wood = getattr(agent, "wood", 0) if agent is not None else 0
    return carried_wood + world.colony_storage.wood >= priority.wood_cost or world.colony_storage.building_materials > 0


def _agent_key(agent) -> str:
    return agent.agent_id or agent.name
