from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.building_placement import find_build_site_near_settlement
from src.building_priorities import SHELTER, shelter_wood_cost_for_agent
from src.config import (
    AGENT_FOOD_CARRY_CAPACITY,
    AGENT_WATER_CARRY_CAPACITY,
    AGENT_WOOD_CARRY_CAPACITY,
    TASK_BUILD_TICKS,
    TASK_CHOP_WOOD_TICKS,
    TASK_COLLECT_WATER_TICKS,
    TASK_DEPOSIT_TICKS,
    TASK_DRINK_TICKS,
    TASK_EAT_TICKS,
    TASK_EXPLORE_TICKS,
    TASK_FATIGUE_INTERRUPT_THRESHOLD,
    TASK_HARVEST_TICKS,
    TASK_HUNGER_INTERRUPT_THRESHOLD,
    TASK_SLEEP_TICKS,
    TASK_THIRST_INTERRUPT_THRESHOLD,
    TICKS_PER_DAY,
)
from src.roles import WOOD
from src.settlement import (
    FOOD,
    WATER,
    deposit_to_stockpile,
    is_adjacent_to_stockpile,
    random_tile_near_settlement,
    stockpile_access_tile,
    stockpile_for,
    withdraw_from_stockpile,
)
from src.settlement_planner import (
    WORK_CONSTRUCTION,
    WORK_EXPLORATION,
    WORK_FOOD,
    WORK_SUPPORT,
    WORK_WATER,
    WORK_WOOD,
    assignment_for,
)

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


DAILY_ROLE_GATHER_FOOD = WORK_FOOD

PHASE_MORNING = "morning"
PHASE_DAY = "day"
PHASE_EVENING = "evening"
PHASE_NIGHT = "night"

STATE_IDLE = "idle"
STATE_MOVING_TO_TARGET = "moving_to_target"
STATE_HARVESTING = "harvesting"
STATE_COLLECTING_WATER = "collecting_water"
STATE_CHOPPING_WOOD = "chopping_wood"
STATE_MOVING_TO_STORAGE = "moving_to_storage"
STATE_DEPOSITING = "depositing"
STATE_BUILDING = "building"
STATE_EXPLORING = "exploring"
STATE_RETURNING_HOME = "returning_home"
STATE_HANDLING_NEED = "handling_need"
STATE_DRINKING = "drinking"
STATE_SLEEPING = "sleeping"


def assign_daily_role(agent: Agent, world: World):
    if not agent.alive:
        return
    agent.daily_role = assignment_for(world, agent) or WORK_FOOD
    if agent.task_state == "":
        agent.task_state = STATE_IDLE


def run_villager_task(agent: Agent, world: World) -> bool:
    if not agent.alive:
        return False

    if agent.daily_role is None:
        assign_daily_role(agent, world)

    if _handle_needs(agent, world):
        return True
    if _run_day_phase(agent, world):
        return True

    assignment = assignment_for(world, agent) or agent.daily_role or WORK_FOOD
    agent.daily_role = assignment

    if assignment == WORK_FOOD:
        return _run_gather_food_task(agent, world)
    if assignment == WORK_WATER:
        return _run_water_task(agent, world)
    if assignment == WORK_WOOD:
        return _run_wood_task(agent, world)
    if assignment == WORK_CONSTRUCTION:
        return _run_construction_task(agent, world)
    if assignment == WORK_EXPLORATION:
        return _run_exploration_task(agent, world)
    if assignment == WORK_SUPPORT:
        return _run_support_task(agent, world)

    return False


def village_phase(world: World) -> str:
    day_tick = world.tick % TICKS_PER_DAY
    if day_tick < TICKS_PER_DAY * 0.2:
        return PHASE_MORNING
    if day_tick < TICKS_PER_DAY * 0.7:
        return PHASE_DAY
    if day_tick < TICKS_PER_DAY * 0.88:
        return PHASE_EVENING
    return PHASE_NIGHT


def _handle_needs(agent: Agent, world: World) -> bool:
    if agent.task_state == STATE_HANDLING_NEED:
        return _continue_eating(agent, world)
    if agent.task_state == STATE_DRINKING:
        return _continue_drinking(agent, world)
    if agent.task_state == STATE_SLEEPING:
        return _continue_sleeping(agent, world)

    if agent.hunger >= TASK_HUNGER_INTERRUPT_THRESHOLD and (agent.food > 0 or world.colony_storage.food > 0):
        _interrupt(agent, STATE_HANDLING_NEED, TASK_EAT_TICKS)
        agent.current_action = "Eating"
        agent.current_goal = "Handle hunger"
        return True
    if agent.hunger >= TASK_HUNGER_INTERRUPT_THRESHOLD:
        return _seek_food_to_eat(agent, world)

    if agent.thirst >= TASK_THIRST_INTERRUPT_THRESHOLD:
        if agent.water > 0 or world.colony_storage.water > 0:
            _interrupt(agent, STATE_DRINKING, TASK_DRINK_TICKS)
            agent.current_action = "Drinking"
            agent.current_goal = "Handle thirst"
            return True
        return _seek_water_to_drink(agent, world)

    if agent.fatigue >= TASK_FATIGUE_INTERRUPT_THRESHOLD:
        return _return_home_or_sleep(agent, world, urgent=True)

    return False


def _run_day_phase(agent: Agent, world: World) -> bool:
    phase = village_phase(world)
    if phase in (PHASE_MORNING, PHASE_DAY) and agent.task_state in (STATE_RETURNING_HOME, STATE_SLEEPING):
        if agent.fatigue < TASK_FATIGUE_INTERRUPT_THRESHOLD:
            agent.task_state = STATE_IDLE
            agent.task_timer = 0
            agent.task_resume_state = None
            agent.current_target = None
            agent.current_path = []
            return False
    if phase == PHASE_NIGHT:
        return _return_home_or_sleep(agent, world, urgent=False)
    if phase == PHASE_EVENING and agent.task_state in (STATE_IDLE, STATE_RETURNING_HOME, STATE_SLEEPING):
        return _return_home_or_sleep(agent, world, urgent=False)
    return False


def _continue_eating(agent: Agent, world: World) -> bool:
    agent.current_action = "Eating"
    agent.current_goal = "Handle hunger"
    agent.task_timer -= 1
    if agent.task_timer > 0:
        return True

    if agent.food > 0:
        agent.food -= 1
        agent.hunger = max(0, agent.hunger - 60)
    elif world.colony_storage.food > 0:
        withdrawn = world.colony_storage.withdraw_food(1)
        withdraw_from_stockpile(world, FOOD, withdrawn)
        if withdrawn > 0:
            agent.hunger = max(0, agent.hunger - 60)

    _resume_task(agent)
    return True


def _continue_drinking(agent: Agent, world: World) -> bool:
    agent.current_action = "Drinking"
    agent.current_goal = "Handle thirst"
    agent.task_timer -= 1
    if agent.task_timer > 0:
        return True

    if agent.water > 0:
        agent.water -= 1
        agent.thirst = 0
    elif world.colony_storage.water > 0:
        withdrawn = world.colony_storage.withdraw_water(1)
        if withdrawn > 0:
            agent.thirst = 0
    elif world.nearby_tile_kind(agent.x, agent.y, WATER):
        agent.thirst = 0

    _resume_task(agent)
    return True


def _continue_sleeping(agent: Agent, world: World) -> bool:
    agent.current_action = "Sleeping"
    agent.current_goal = "Rest"
    agent.task_timer -= 1
    if agent.task_timer > 0:
        return True

    agent.fatigue = 0
    agent.task_state = STATE_IDLE
    agent.task_timer = 0
    agent.task_resume_state = None
    agent.reset_stuck()
    return True


def _seek_water_to_drink(agent: Agent, world: World) -> bool:
    target = _choose_water_target(agent, world)
    if target is None:
        return False
    if _move_to_target(agent, world, target, "Seeking water", "Handle thirst"):
        return True
    if world.nearby_tile_kind(agent.x, agent.y, WATER):
        _interrupt(agent, STATE_DRINKING, TASK_DRINK_TICKS)
        return True
    return False


def _seek_food_to_eat(agent: Agent, world: World) -> bool:
    target = _choose_resource_target(agent, world, FOOD)
    if target is None:
        return False

    if agent.task_resume_state is None:
        agent.task_resume_state = agent.task_state if agent.task_state not in (STATE_IDLE, STATE_HANDLING_NEED) else STATE_IDLE

    agent.task_target = target
    if (agent.x, agent.y) == target:
        if agent.task_state != STATE_HARVESTING:
            agent.task_state = STATE_HARVESTING
            agent.task_timer = TASK_HARVEST_TICKS
            agent.current_target = None
            agent.current_path = []
        agent.current_action = "Harvesting"
        agent.current_goal = "Handle hunger"
        return _collect_resource(agent, world, FOOD, "Harvesting")

    agent.task_state = STATE_MOVING_TO_TARGET
    return _move_to_target(agent, world, target, "Seeking food", "Handle hunger")


def _return_home_or_sleep(agent: Agent, world: World, urgent: bool) -> bool:
    home = _home_anchor(agent, world)
    if (agent.x, agent.y) != home:
        agent.task_state = STATE_RETURNING_HOME
        return _move_to_target(agent, world, home, "Returning home", "Rest")

    if urgent or village_phase(world) == PHASE_NIGHT:
        agent.task_state = STATE_SLEEPING
        agent.task_timer = TASK_SLEEP_TICKS
        agent.current_action = "Sleeping"
        agent.current_goal = "Rest"
        agent.current_target = None
        agent.current_path = []
        return True

    agent.current_action = "At home"
    agent.current_goal = "Evening"
    return True


def _run_gather_food_task(agent: Agent, world: World) -> bool:
    return _run_resource_task(
        agent,
        world,
        resource_type=FOOD,
        collect_state=STATE_HARVESTING,
        collect_action="Harvesting",
        move_action="Moving to food",
        collect_ticks=TASK_HARVEST_TICKS,
    )


def _run_water_task(agent: Agent, world: World) -> bool:
    return _run_resource_task(
        agent,
        world,
        resource_type=WATER,
        collect_state=STATE_COLLECTING_WATER,
        collect_action="Collecting water",
        move_action="Moving to water",
        collect_ticks=TASK_COLLECT_WATER_TICKS,
    )


def _run_wood_task(agent: Agent, world: World) -> bool:
    return _run_resource_task(
        agent,
        world,
        resource_type=WOOD,
        collect_state=STATE_CHOPPING_WOOD,
        collect_action="Chopping wood",
        move_action="Moving to wood",
        collect_ticks=TASK_CHOP_WOOD_TICKS,
    )


def _run_resource_task(
    agent: Agent,
    world: World,
    resource_type: str,
    collect_state: str,
    collect_action: str,
    move_action: str,
    collect_ticks: int,
) -> bool:
    if agent.task_state == STATE_IDLE:
        if _carried_amount(agent, resource_type) > 0:
            agent.task_state = STATE_MOVING_TO_STORAGE
            agent.task_timer = 0
            return _move_to_storage(agent, world, resource_type)

        target = _choose_resource_target(agent, world, resource_type)
        if target is None:
            return False
        agent.task_target = target
        agent.task_state = STATE_MOVING_TO_TARGET
        agent.task_timer = 0

    if agent.task_state == STATE_MOVING_TO_TARGET:
        target = agent.task_target
        if target is None or not _resource_available(world, target, resource_type):
            _clear_task_target(agent)
            return False
        if _arrived_for_resource(agent, world, target, resource_type):
            agent.task_state = collect_state
            agent.task_timer = collect_ticks
            agent.current_target = None
            agent.current_path = []
            return True
        return _move_to_target(agent, world, target, move_action, _goal_for_resource(resource_type))

    if agent.task_state == collect_state:
        return _collect_resource(agent, world, resource_type, collect_action)
    if agent.task_state == STATE_MOVING_TO_STORAGE:
        return _move_to_storage(agent, world, resource_type)
    if agent.task_state == STATE_DEPOSITING:
        return _deposit_resource(agent, world, resource_type)

    return False


def _collect_resource(agent: Agent, world: World, resource_type: str, action_name: str) -> bool:
    target = agent.task_target
    if target is None or not _resource_available(world, target, resource_type):
        _clear_task_target(agent)
        return False

    agent.current_action = action_name
    agent.current_goal = _goal_for_resource(resource_type)
    agent.task_timer -= 1
    if agent.task_timer > 0:
        return True

    if resource_type == FOOD:
        world.tile_at(*target).food -= 1
        agent.food += 1
        agent.remembered_food.add(target)
        world.colony_memory.remember_food(target)
    elif resource_type == WATER:
        agent.water += 1
        agent.remembered_water.add(target)
        world.colony_memory.remember_water(target)
    elif resource_type == WOOD:
        world.tile_at(*target).wood -= 1
        agent.wood += 1
        agent.remembered_wood.add(target)
        world.colony_memory.remember_wood(target)

    if not _resource_available(world, target, resource_type):
        _forget_resource_target(agent, world, target, resource_type)

    if _should_continue_collecting(agent, world, target, resource_type):
        agent.task_state = _collect_state_for_resource(resource_type)
        agent.task_timer = _collect_ticks_for_resource(resource_type)
    else:
        agent.task_target = None
        agent.current_target = None
        agent.current_path = []
        agent.task_state = STATE_MOVING_TO_STORAGE
        agent.task_timer = 0
    agent.reset_stuck()
    return True


def _move_to_storage(agent: Agent, world: World, resource_type: str) -> bool:
    if _carried_amount(agent, resource_type) <= 0:
        agent.task_state = STATE_IDLE
        return True

    if resource_type == WATER or stockpile_for(world, resource_type) is None:
        agent.task_state = STATE_DEPOSITING
        agent.task_timer = TASK_DEPOSIT_TICKS
        return True

    agent.current_action = "Moving to storage"
    agent.current_goal = _deposit_goal_for_resource(resource_type)
    if is_adjacent_to_stockpile(world, agent.x, agent.y, resource_type):
        agent.task_state = STATE_DEPOSITING
        agent.task_timer = TASK_DEPOSIT_TICKS
        agent.current_target = None
        agent.current_path = []
        return True

    target = stockpile_access_tile(world, resource_type, agent)
    if target is None:
        return False
    return _move_to_target(agent, world, target, "Moving to storage", _deposit_goal_for_resource(resource_type))


def _deposit_resource(agent: Agent, world: World, resource_type: str) -> bool:
    agent.current_action = "Depositing"
    agent.current_goal = _deposit_goal_for_resource(resource_type)
    agent.task_timer -= 1
    if agent.task_timer > 0:
        return True

    if resource_type == FOOD:
        keep = 1 if agent.hunger >= 30 else 0
        amount = max(0, agent.food - keep)
        deposited = world.colony_storage.deposit_food(amount)
        deposit_to_stockpile(world, FOOD, deposited)
        agent.food -= deposited
    elif resource_type == WATER:
        keep = 1 if agent.thirst >= 30 else 0
        amount = max(0, agent.water - keep)
        deposited = world.colony_storage.deposit_water(amount)
        agent.water -= deposited
    elif resource_type == WOOD:
        deposited = world.colony_storage.deposit_wood(agent.wood)
        deposit_to_stockpile(world, WOOD, deposited)
        agent.wood -= deposited

    agent.task_state = STATE_IDLE
    agent.task_timer = 0
    agent.reset_stuck()
    return True


def _run_construction_task(agent: Agent, world: World) -> bool:
    if world.building_priority() is None:
        agent.task_state = STATE_IDLE
        return False

    if agent.task_state == STATE_IDLE:
        if not _construction_materials_available(agent, world):
            return False
        target = find_build_site_near_settlement(world, SHELTER, agent)
        if target is None:
            return False
        agent.task_target = target
        agent.task_state = STATE_MOVING_TO_TARGET

    if agent.task_state == STATE_MOVING_TO_TARGET:
        target = agent.task_target
        if target is None:
            return False
        if (agent.x, agent.y) == target:
            agent.task_state = STATE_BUILDING
            agent.task_timer = TASK_BUILD_TICKS
            agent.current_target = None
            agent.current_path = []
            return True
        return _move_to_target(agent, world, target, "Moving to build site", "Build shelter")

    if agent.task_state == STATE_BUILDING:
        return _build_shelter(agent, world)

    return False


def _build_shelter(agent: Agent, world: World) -> bool:
    target = agent.task_target
    if target is None or (agent.x, agent.y) != target:
        agent.task_state = STATE_IDLE
        return False
    if world.settlement is None:
        agent.task_state = STATE_IDLE
        return False
    if world.tile_at(*target).kind == SHELTER:
        world.settlement.construction_progress.pop(target, None)
        agent.task_target = None
        agent.task_state = STATE_IDLE
        return True

    agent.current_action = "Building"
    agent.current_goal = "Build shelter"
    progress = world.settlement.construction_progress.get(target, 0) + 1
    world.settlement.construction_progress[target] = progress
    agent.task_timer = max(0, TASK_BUILD_TICKS - progress)
    if progress < TASK_BUILD_TICKS:
        return True

    cost = shelter_wood_cost_for_agent(agent, world)
    carried = min(agent.wood, cost)
    agent.wood -= carried
    remaining = cost - carried
    withdrawn = world.colony_storage.withdraw_wood(remaining)
    withdraw_from_stockpile(world, WOOD, withdrawn)
    if carried + withdrawn < cost:
        agent.wood += carried
        if withdrawn > 0:
            returned = world.colony_storage.deposit_wood(withdrawn)
            deposit_to_stockpile(world, WOOD, returned)
        agent.task_state = STATE_IDLE
        agent.task_timer = 0
        return False

    if world.colony_storage.building_materials > 0:
        world.colony_storage.withdraw_building_materials(1)

    world.tile_at(*target).kind = SHELTER
    world.settlement.construction_progress.pop(target, None)
    agent.task_target = None
    agent.current_target = None
    agent.current_path = []
    agent.task_state = STATE_IDLE
    agent.task_timer = 0
    agent.reset_stuck()
    world.log(f"{agent.name} builds a shelter.")
    return True


def _construction_materials_available(agent: Agent, world: World) -> bool:
    priority = world.building_priority()
    if priority is None:
        return False
    cost = shelter_wood_cost_for_agent(agent, world)
    return agent.wood + world.colony_storage.wood >= cost or world.colony_storage.building_materials > 0


def _run_exploration_task(agent: Agent, world: World) -> bool:
    if agent.task_state == STATE_IDLE:
        target = random_tile_near_settlement(world, random.Random(f"{world.seed}|explore|{world.day}|{agent.agent_id or agent.name}"), agent.role)
        if target is None:
            return False
        agent.task_target = target
        agent.task_state = STATE_MOVING_TO_TARGET

    if agent.task_state == STATE_MOVING_TO_TARGET:
        target = agent.task_target
        if target is None:
            return False
        if (agent.x, agent.y) == target:
            agent.task_state = STATE_EXPLORING
            agent.task_timer = TASK_EXPLORE_TICKS
            return True
        return _move_to_target(agent, world, target, "Exploring", "Explore")

    if agent.task_state == STATE_EXPLORING:
        agent.current_action = "Exploring"
        agent.current_goal = "Explore"
        agent.task_timer -= 1
        agent.scan_surroundings(world)
        if agent.task_timer > 0:
            return True
        agent.task_target = None
        agent.task_state = STATE_IDLE
        return True

    return False


def _run_support_task(agent: Agent, world: World) -> bool:
    if world.colony_storage.food <= len(world.living_agents()):
        return _run_gather_food_task(agent, world)
    if world.colony_storage.wood < 4:
        return _run_wood_task(agent, world)
    return False


def _move_to_target(agent: Agent, world: World, target: tuple[int, int], action: str, goal: str) -> bool:
    from src.actions import _step_along_path

    agent.current_action = action
    agent.current_goal = goal
    return _step_along_path(agent, world, target)


def _interrupt(agent: Agent, state: str, timer: int):
    if agent.task_resume_state is None:
        agent.task_resume_state = agent.task_state if agent.task_state not in (state, STATE_IDLE) else STATE_IDLE
    agent.task_state = state
    agent.task_timer = timer
    agent.current_target = None
    agent.current_path = []


def _resume_task(agent: Agent):
    agent.task_state = agent.task_resume_state or STATE_IDLE
    agent.task_resume_state = None
    agent.task_timer = 0
    agent.current_target = None
    agent.current_path = []
    agent.reset_stuck()


def _choose_resource_target(agent: Agent, world: World, resource_type: str) -> tuple[int, int] | None:
    if resource_type == FOOD:
        remembered = agent.remembered_food | world.colony_memory.known_food
    elif resource_type == WATER:
        remembered = agent.remembered_water | world.colony_memory.known_water
    else:
        remembered = agent.remembered_wood | world.colony_memory.known_wood

    candidates = [pos for pos in remembered if _resource_available(world, pos, resource_type)]
    if not candidates:
        candidates = _scan_resource_near_home(agent, world, resource_type)
    if not candidates:
        return None
    return world.choose_resource_target(agent, resource_type, set(candidates)) or min(
        candidates,
        key=lambda pos: (_distance(pos, (agent.x, agent.y)), _distance(pos, _home_anchor(agent, world)), pos[1], pos[0]),
    )


def _choose_water_target(agent: Agent, world: World) -> tuple[int, int] | None:
    return _choose_resource_target(agent, world, WATER)


def _scan_resource_near_home(agent: Agent, world: World, resource_type: str) -> list[tuple[int, int]]:
    anchor_x, anchor_y = _home_anchor(agent, world)
    radius = max(4, getattr(agent, "home_wander_radius", 4) + agent.discovery_radius(resource_type))
    candidates = []
    for y in range(max(0, anchor_y - radius), min(world.height, anchor_y + radius + 1)):
        for x in range(max(0, anchor_x - radius), min(world.width, anchor_x + radius + 1)):
            if max(abs(x - anchor_x), abs(y - anchor_y)) > radius:
                continue
            if _resource_available(world, (x, y), resource_type):
                candidates.append((x, y))
    return candidates


def _resource_available(world: World, pos: tuple[int, int], resource_type: str) -> bool:
    x, y = pos
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    tile = world.tile_at(x, y)
    if resource_type == FOOD:
        return tile.walkable and tile.food > 0
    if resource_type == WATER:
        return tile.kind == WATER
    if resource_type == WOOD:
        return tile.walkable and tile.wood > 0
    return False


def _arrived_for_resource(agent: Agent, world: World, target: tuple[int, int], resource_type: str) -> bool:
    if resource_type == WATER:
        return world.nearby_tile_kind(agent.x, agent.y, WATER)
    return (agent.x, agent.y) == target


def _carried_amount(agent: Agent, resource_type: str) -> int:
    if resource_type == FOOD:
        return agent.food
    if resource_type == WATER:
        return agent.water
    if resource_type == WOOD:
        return agent.wood
    return 0


def _carry_capacity(resource_type: str) -> int:
    if resource_type == FOOD:
        return AGENT_FOOD_CARRY_CAPACITY
    if resource_type == WATER:
        return AGENT_WATER_CARRY_CAPACITY
    if resource_type == WOOD:
        return AGENT_WOOD_CARRY_CAPACITY
    return 1


def _should_continue_collecting(agent: Agent, world: World, target: tuple[int, int], resource_type: str) -> bool:
    if _carried_amount(agent, resource_type) >= _carry_capacity(resource_type):
        return False
    if resource_type == FOOD and agent.hunger >= TASK_HUNGER_INTERRUPT_THRESHOLD:
        return False
    if resource_type == WATER and agent.thirst >= TASK_THIRST_INTERRUPT_THRESHOLD:
        return False
    return _resource_available(world, target, resource_type)


def _collect_state_for_resource(resource_type: str) -> str:
    if resource_type == FOOD:
        return STATE_HARVESTING
    if resource_type == WATER:
        return STATE_COLLECTING_WATER
    if resource_type == WOOD:
        return STATE_CHOPPING_WOOD
    return STATE_IDLE


def _collect_ticks_for_resource(resource_type: str) -> int:
    if resource_type == FOOD:
        return TASK_HARVEST_TICKS
    if resource_type == WATER:
        return TASK_COLLECT_WATER_TICKS
    if resource_type == WOOD:
        return TASK_CHOP_WOOD_TICKS
    return 1


def _goal_for_resource(resource_type: str) -> str:
    if resource_type == FOOD:
        return "Gather food"
    if resource_type == WATER:
        return "Collect water"
    if resource_type == WOOD:
        return "Gather wood"
    return "Work"


def _deposit_goal_for_resource(resource_type: str) -> str:
    if resource_type == FOOD:
        return "Deposit food"
    if resource_type == WATER:
        return "Deposit water"
    if resource_type == WOOD:
        return "Deposit wood"
    return "Deposit"


def _home_anchor(agent: Agent, world: World) -> tuple[int, int]:
    if agent.home_x is not None and agent.home_y is not None:
        return agent.home_x, agent.home_y
    if world.settlement is not None:
        return world.settlement.x, world.settlement.y
    return agent.x, agent.y


def _distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _clear_task_target(agent: Agent):
    agent.task_target = None
    agent.current_target = None
    agent.current_path = []
    agent.task_state = STATE_IDLE
    agent.task_timer = 0


def _forget_resource_target(agent: Agent, world: World, pos: tuple[int, int], resource_type: str):
    if resource_type == FOOD:
        agent.remembered_food.discard(pos)
        world.colony_memory.forget_food(pos)
    elif resource_type == WATER:
        agent.remembered_water.discard(pos)
        world.colony_memory.forget_water(pos)
    elif resource_type == WOOD:
        agent.remembered_wood.discard(pos)
        world.colony_memory.forget_wood(pos)
