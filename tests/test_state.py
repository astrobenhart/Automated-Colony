from src.actions import GatherFoodAction
from src.agent import Agent
from src.lifecycle import ADULT, ELDER
from src.roles import BUILDER, GENERALIST
from src.state import (
    CONTENT,
    DEAD,
    EXPLORING,
    HUNGRY,
    IDLE,
    RECOVERING,
    RESTING,
    THIRSTY,
    TIRED,
    WORKING,
    state_label,
)
from src.tile import Tile
from src.traits import CALM, LAZY
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_healthy_villager_state_is_content():
    agent = Agent("Ari", 1, 1)

    assert state_label(agent) == CONTENT


def test_thirsty_villager_state_is_thirsty():
    agent = Agent("Ari", 1, 1, thirst=50, hunger=80)

    assert state_label(agent) == THIRSTY


def test_hungry_villager_state_is_hungry():
    agent = Agent("Ari", 1, 1, hunger=50)

    assert state_label(agent) == HUNGRY


def test_tired_villager_state_is_tired():
    agent = Agent("Ari", 1, 1, fatigue=70)

    assert state_label(agent) == TIRED


def test_recovering_villager_state_is_recovering():
    agent = Agent("Ari", 1, 1, current_action="Recovering", thirst=90)

    assert state_label(agent) == RECOVERING


def test_dead_villager_state_is_dead():
    agent = Agent("Ari", 1, 1, alive=False, current_action="Dead")

    assert state_label(agent) == DEAD


def test_resting_villager_state_is_resting():
    agent = Agent("Ari", 1, 1, current_action="Sleeping")

    assert state_label(agent) == RESTING


def test_working_villager_state_is_working():
    agent = Agent("Ari", 1, 1, current_action="Gathering food")

    assert state_label(agent) == WORKING


def test_exploring_villager_state_is_exploring():
    agent = Agent("Ari", 1, 1, current_action="Wandering")

    assert state_label(agent) == EXPLORING


def test_idle_villager_state_is_idle_when_mild_needs_exist():
    agent = Agent("Ari", 1, 1, current_action="Idle", hunger=5)

    assert state_label(agent) == IDLE


def test_state_priority_shows_need_before_working():
    agent = Agent("Ari", 1, 1, current_action="Gathering wood", hunger=55)

    assert state_label(agent) == HUNGRY


def test_traits_do_not_affect_state():
    calm = Agent("Ari", 1, 1, trait=CALM, current_action="Idle")
    lazy = Agent("Bryn", 1, 1, trait=LAZY, current_action="Idle")

    assert state_label(calm) == state_label(lazy) == CONTENT


def test_lifecycle_does_not_affect_state():
    adult = Agent("Ari", 1, 1, lifecycle_stage=ADULT, current_action="Idle")
    elder = Agent("Bryn", 1, 1, lifecycle_stage=ELDER, current_action="Idle")

    assert state_label(adult) == state_label(elder) == CONTENT


def test_state_label_does_not_modify_behavior():
    world = make_world()
    world.tiles[2][2].food = 1
    generalist = Agent("Ari", 2, 2, role=GENERALIST)
    builder = Agent("Bryn", 2, 2, role=BUILDER)
    before = (generalist.current_goal, generalist.current_action, generalist.hunger)

    assert state_label(generalist, world) == CONTENT
    assert (generalist.current_goal, generalist.current_action, generalist.hunger) == before

    world.agents.append(generalist)
    generalist_action = generalist.choose_action(world)
    world.agents.remove(generalist)
    world.agents.append(builder)
    builder_action = builder.choose_action(world)

    assert isinstance(generalist_action, GatherFoodAction)
    assert isinstance(builder_action, GatherFoodAction)
