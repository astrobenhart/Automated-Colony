from src.actions import DepositFoodAction, DepositWoodAction, EatFromStorageAction
from src.agent import Agent
from src.colony_storage import ColonyStorage
from src.tile import Tile
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def add_shelters(world: World, positions: list[tuple[int, int]]):
    for x, y in positions:
        world.tiles[y][x].kind = "shelter"


def test_colony_storage_starts_empty():
    storage = ColonyStorage()

    assert storage.food == 0
    assert storage.wood == 0


def test_deposit_and_withdraw_food():
    storage = ColonyStorage()

    assert storage.deposit_food(3) == 3
    assert storage.food == 3
    assert storage.withdraw_food(2) == 2
    assert storage.food == 1
    assert storage.withdraw_food(5) == 1
    assert storage.food == 0
    assert storage.withdraw_food(1) == 0


def test_deposit_and_withdraw_wood():
    storage = ColonyStorage()

    assert storage.deposit_wood(4) == 4
    assert storage.wood == 4
    assert storage.withdraw_wood(2) == 2
    assert storage.wood == 2
    assert storage.withdraw_wood(5) == 2
    assert storage.wood == 0
    assert storage.withdraw_wood(1) == 0


def test_world_storage_starts_empty():
    world = make_world()

    assert world.colony_storage.food == 0
    assert world.colony_storage.wood == 0


def test_agent_with_extra_food_can_deposit_food():
    world = make_world()
    agent = Agent("Ari", 2, 2, food=3)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Deposit food"
    assert isinstance(action, DepositFoodAction)

    action.execute(agent, world)

    assert agent.food == 1
    assert world.colony_storage.food == 2


def test_agent_deposits_wood_when_construction_need_is_low():
    world = make_world()
    add_shelters(world, [(0, 0)])
    agent = Agent("Ari", 2, 2, wood=2)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert not world.needs_more_shelters()
    assert agent.current_goal == "Deposit wood"
    assert isinstance(action, DepositWoodAction)

    action.execute(agent, world)

    assert agent.wood == 0
    assert world.colony_storage.wood == 2


def test_hungry_agent_with_no_food_can_eat_from_storage():
    world = make_world()
    world.colony_storage.deposit_food(2)
    agent = Agent("Ari", 2, 2, hunger=80, food=0)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Eat from storage"
    assert isinstance(action, EatFromStorageAction)

    action.execute(agent, world)

    assert agent.hunger == 20
    assert agent.food == 0
    assert world.colony_storage.food == 1


def test_carried_food_is_preferred_over_storage_food():
    world = make_world()
    world.colony_storage.deposit_food(2)
    agent = Agent("Ari", 2, 2, hunger=80, food=1)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Eat"
    assert not isinstance(action, EatFromStorageAction)
