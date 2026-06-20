from src.agent import Agent
from src.settlement import FOOD, Settlement, Stockpile
from src.task_behavior import (
    DAILY_ROLE_GATHER_FOOD,
    PHASE_NIGHT,
    STATE_DEPOSITING,
    STATE_HANDLING_NEED,
    STATE_HARVESTING,
    STATE_IDLE,
    STATE_MOVING_TO_STORAGE,
    STATE_MOVING_TO_TARGET,
    STATE_RETURNING_HOME,
    STATE_CHOPPING_WOOD,
    STATE_COLLECTING_WATER,
    assign_daily_role,
    run_villager_task,
    village_phase,
)
from src.settlement_planner import WORK_EXPLORATION, WORK_FOOD, WORK_WATER, WORK_WOOD
from src.roles import FORAGER
from src.tile import Tile
from src.world import World, create_world


def make_world(width=12, height=12):
    world = World(width, height, seed=123)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement(
        "Willowhold",
        width // 2,
        height // 2,
        1,
        "Spring",
        stockpiles=[Stockpile(width // 2, width // 2 + 1, FOOD)],
    )
    return world


def test_spawned_villagers_receive_settlement_work_assignments():
    world = create_world(seed=82, agent_count=12)

    assignments = {agent.daily_role for agent in world.agents}
    assert world.settlement.last_planned_day == world.day
    assert all(agent.daily_role for agent in world.agents)
    assert assignments <= {WORK_FOOD, WORK_WATER, WORK_EXPLORATION}
    assert {WORK_FOOD, WORK_WATER} <= assignments
    assert len(assignments) > 1


def test_daily_role_assignment_is_infrequent_and_persistent():
    world = make_world()
    agent = Agent("Ari", 5, 5)

    assign_daily_role(agent, world)
    assert agent.daily_role == DAILY_ROLE_GATHER_FOOD
    assert agent.task_state == STATE_IDLE


def test_forager_can_receive_water_collection_from_settlement_planner():
    world = make_world()
    world.settlement.local_water = set()
    agent = Agent("Fenn", 5, 5, role=FORAGER)
    world.agents.append(agent)
    world.plan_settlement_work()

    assert agent.daily_role in {WORK_FOOD, WORK_WATER}


def test_food_task_selects_target_without_old_decision_loop():
    world = make_world()
    world.colony_storage.deposit_food(20)
    world.colony_storage.deposit_water(20)
    world.tile_at(7, 5).food = 2
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5, home_wander_radius=3)
    world.agents.append(agent)
    agent.daily_role = WORK_FOOD

    assert run_villager_task(agent, world)

    assert agent.task_state == STATE_MOVING_TO_TARGET
    assert agent.task_target == (7, 5)
    assert agent.current_goal == "Gather food"
    assert agent.last_decision_tick == -1


def test_harvesting_takes_multiple_task_ticks():
    world = make_world()
    world.tile_at(5, 5).food = 1
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD
    agent.task_state = STATE_HARVESTING
    agent.task_target = (5, 5)
    agent.task_timer = 2

    assert run_villager_task(agent, world)
    assert agent.food == 0
    assert world.tile_at(5, 5).food == 1

    assert run_villager_task(agent, world)
    assert agent.food == 1
    assert world.tile_at(5, 5).food == 0
    assert agent.task_state == STATE_MOVING_TO_STORAGE


def test_depositing_takes_multiple_task_ticks_and_stores_food():
    world = make_world()
    agent = Agent("Ari", 6, 6, food=2)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD
    agent.task_state = STATE_DEPOSITING
    agent.task_timer = 2

    assert run_villager_task(agent, world)
    assert world.colony_storage.food == 0
    assert agent.food == 2

    assert run_villager_task(agent, world)
    assert world.colony_storage.food == 2
    assert world.settlement.stockpile_for(FOOD).stored_amount == 2
    assert agent.food == 0
    assert agent.task_state == STATE_IDLE


def test_storage_move_state_transitions_to_depositing_when_adjacent():
    world = make_world()
    agent = Agent("Ari", 6, 6, food=1)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD
    agent.task_state = STATE_MOVING_TO_STORAGE

    assert run_villager_task(agent, world)

    assert agent.task_state == STATE_DEPOSITING
    assert agent.current_goal == "Deposit food"


def test_hunger_interrupt_eats_then_resumes_previous_task():
    world = make_world()
    agent = Agent("Ari", 5, 5, hunger=80, food=1)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD
    agent.task_state = STATE_MOVING_TO_TARGET
    agent.task_target = (7, 5)

    assert run_villager_task(agent, world)
    assert agent.task_state == STATE_HANDLING_NEED
    assert agent.task_resume_state == STATE_MOVING_TO_TARGET

    assert run_villager_task(agent, world)

    assert agent.hunger == 20
    assert agent.food == 0
    assert agent.task_state == STATE_MOVING_TO_TARGET


def test_critical_hunger_without_stored_food_interrupts_to_seek_food():
    world = make_world()
    world.tile_at(8, 5).food = 2
    agent = Agent("Ari", 5, 5, hunger=80, home_x=5, home_y=5)
    agent.daily_role = WORK_WOOD
    agent.task_state = STATE_CHOPPING_WOOD
    agent.task_target = (5, 5)
    agent.task_timer = 4
    world.agents.append(agent)

    assert run_villager_task(agent, world)

    assert agent.current_goal == "Handle hunger"
    assert agent.current_action == "Seeking food"
    assert agent.task_resume_state == STATE_CHOPPING_WOOD
    assert agent.task_target == (8, 5)


def test_moderate_thirst_does_not_cancel_daily_work():
    world = make_world()
    world.tile_at(7, 5).food = 2
    agent = Agent("Ari", 5, 5, thirst=60, home_x=5, home_y=5)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD

    assert run_villager_task(agent, world)
    assert agent.task_state == STATE_MOVING_TO_TARGET


def test_critical_thirst_interrupts_work_to_drink_carried_water():
    world = make_world()
    agent = Agent("Ari", 5, 5, thirst=80, water=1)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD
    agent.task_state = STATE_MOVING_TO_TARGET
    agent.task_target = (7, 5)

    assert run_villager_task(agent, world)
    assert agent.current_goal == "Handle thirst"

    assert run_villager_task(agent, world)
    assert agent.thirst == 0
    assert agent.task_state == STATE_MOVING_TO_TARGET


def test_water_collection_uses_multi_tick_collect_state():
    world = make_world()
    world.tile_at(8, 5).kind = "water"
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = WORK_WATER

    assert run_villager_task(agent, world)
    assert agent.task_state == STATE_MOVING_TO_TARGET

    for _ in range(4):
        run_villager_task(agent, world)
        if agent.task_state == STATE_COLLECTING_WATER:
            break
    assert agent.task_state == STATE_COLLECTING_WATER


def test_wood_assignment_uses_chopping_state():
    world = make_world()
    world.tile_at(5, 5).wood = 2
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = WORK_WOOD
    agent.task_state = STATE_CHOPPING_WOOD
    agent.task_target = (5, 5)
    agent.task_timer = 2

    assert run_villager_task(agent, world)
    assert agent.wood == 0

    assert run_villager_task(agent, world)
    assert agent.wood == 1
    assert agent.task_state == STATE_CHOPPING_WOOD

    while agent.task_state != STATE_MOVING_TO_STORAGE:
        assert run_villager_task(agent, world)

    assert agent.wood == 2


def test_wood_worker_delivers_carried_wood_before_gathering_more():
    world = make_world()
    agent = Agent("Ari", 6, 6, wood=1, home_x=5, home_y=5)
    agent.daily_role = WORK_WOOD
    agent.task_state = STATE_IDLE

    assert run_villager_task(agent, world)

    assert agent.task_state in {STATE_MOVING_TO_STORAGE, STATE_DEPOSITING}


def test_food_worker_batches_harvest_until_carry_capacity():
    world = make_world()
    world.tile_at(5, 5).food = 5
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = WORK_FOOD
    agent.task_state = STATE_HARVESTING
    agent.task_target = (5, 5)
    agent.task_timer = 1

    for _ in range(6):
        assert run_villager_task(agent, world)
        if agent.task_state == STATE_MOVING_TO_STORAGE:
            break

    assert agent.food == 3
    assert world.tile_at(5, 5).food == 2
    assert agent.task_state == STATE_MOVING_TO_STORAGE


def test_night_phase_returns_villager_home():
    world = make_world()
    world.tick = 49
    agent = Agent("Ari", 2, 2, home_x=5, home_y=5)
    agent.daily_role = WORK_FOOD

    assert village_phase(world) == PHASE_NIGHT
    assert run_villager_task(agent, world)
    assert agent.task_state == STATE_RETURNING_HOME


def test_failed_build_attempt_returns_withdrawn_storage_wood():
    world = make_world()
    world.colony_storage.deposit_wood(2)
    agent = Agent("Bryn", 5, 5)
    agent.daily_role = "house_construction"
    agent.task_state = "building"
    agent.task_target = (5, 5)
    agent.task_timer = 1

    assert not run_villager_task(agent, world)

    assert world.colony_storage.wood == 2
    assert agent.wood == 0
    assert world.tile_at(5, 5).kind == "grass"


def test_build_progress_persists_on_settlement_site():
    world = make_world()
    world.colony_storage.deposit_food(20)
    world.colony_storage.deposit_water(20)
    world.colony_storage.deposit_wood(3)
    agent = Agent("Bryn", 5, 5)
    agent.daily_role = "house_construction"
    agent.task_state = "building"
    agent.task_target = (5, 5)
    agent.task_timer = 20
    world.agents.append(agent)

    assert run_villager_task(agent, world)
    assert world.settlement.construction_progress[(5, 5)] == 1

    agent.task_state = STATE_RETURNING_HOME
    agent.task_state = "building"
    agent.task_target = (5, 5)
    world.settlement.construction_progress[(5, 5)] = 19

    assert run_villager_task(agent, world)

    assert world.tile_at(5, 5).kind == "shelter"
    assert (5, 5) not in world.settlement.construction_progress


def test_morning_resets_return_home_state_to_daily_work():
    world = make_world()
    world.tick = 1
    world.tile_at(7, 5).food = 1
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = WORK_FOOD
    agent.task_state = STATE_RETURNING_HOME

    assert run_villager_task(agent, world)
    assert agent.task_state == STATE_MOVING_TO_TARGET


def test_task_falls_back_when_no_food_exists():
    world = make_world()
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.daily_role = DAILY_ROLE_GATHER_FOOD

    assert not run_villager_task(agent, world)
    assert agent.task_state == STATE_IDLE
