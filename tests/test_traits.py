from collections import Counter

from src.actions import GatherFoodAction
from src.agent import Agent
from src.config import TICKS_PER_DAY
from src.tile import Tile
from src.traits import (
    BOLD,
    CALM,
    CAUTIOUS,
    CURIOUS,
    DILIGENT,
    FRIENDLY,
    GRUMPY,
    LAZY,
    STUBBORN,
    TIMID,
    TRAITS,
    is_valid_trait,
    trait_for_index,
)
from src.world import World, create_world


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_traits_include_positive_neutral_and_imperfect_labels():
    assert {DILIGENT, FRIENDLY, CALM, CURIOUS}.issubset(TRAITS)
    assert {CAUTIOUS, BOLD}.issubset(TRAITS)
    assert {LAZY, GRUMPY, STUBBORN, TIMID}.issubset(TRAITS)


def test_traits_are_valid_and_assigned_by_static_cycle():
    traits = [trait_for_index(index) for index in range(20)]

    assert all(is_valid_trait(trait) for trait in traits)
    assert set(TRAITS) == {
        DILIGENT,
        CURIOUS,
        CALM,
        FRIENDLY,
        CAUTIOUS,
        BOLD,
        LAZY,
        GRUMPY,
        STUBBORN,
        TIMID,
    }
    assert Counter(traits) == {trait: 2 for trait in TRAITS}


def test_spawned_villagers_receive_one_trait():
    world = create_world(seed=50, agent_count=10)

    assert all(is_valid_trait(agent.trait) for agent in world.agents)
    assert [agent.trait for agent in world.agents] == list(TRAITS)


def test_default_agent_trait_is_calm():
    agent = Agent("Ari", 1, 1)

    assert agent.trait == CALM


def test_imperfect_traits_are_valid_without_penalty_metadata():
    for trait in (LAZY, GRUMPY, STUBBORN, TIMID):
        assert is_valid_trait(trait)
        assert isinstance(trait, str)


def test_trait_assignment_is_deterministic_for_fixed_seed():
    first = create_world(seed=51, agent_count=10)
    second = create_world(seed=51, agent_count=10)

    assert [(agent.name, agent.trait, agent.x, agent.y) for agent in first.agents] == [
        (agent.name, agent.trait, agent.x, agent.y) for agent in second.agents
    ]


def test_trait_remains_unchanged_during_simulation():
    world = create_world(seed=52, agent_count=10)
    initial_traits = [(agent.name, agent.trait) for agent in world.agents]

    for _ in range(TICKS_PER_DAY * 2):
        world.update()

    assert [(agent.name, agent.trait) for agent in world.agents] == initial_traits


def test_traits_do_not_modify_behavior_or_goal_scoring():
    world = make_world()
    world.tiles[2][2].food = 1
    calm = Agent("Ari", 2, 2, trait=CALM)
    lazy = Agent("Bryn", 2, 2, trait=LAZY)

    world.agents.append(calm)
    calm_action = calm.choose_action(world)
    world.agents.remove(calm)

    world.agents.append(lazy)
    lazy_action = lazy.choose_action(world)

    assert isinstance(calm_action, GatherFoodAction)
    assert isinstance(lazy_action, GatherFoodAction)
    assert calm.current_goal == lazy.current_goal == "Gather food"


def test_trait_definitions_do_not_include_gameplay_modifiers():
    for trait in TRAITS:
        assert isinstance(trait, str)
        assert not hasattr(trait, "goal_bonus")
        assert not hasattr(trait, "movement_modifier")
