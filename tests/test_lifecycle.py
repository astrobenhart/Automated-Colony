from collections import Counter

from src.agent import Agent
from src.config import TICKS_PER_DAY
from src.lifecycle import ADULT, ELDER, LIFECYCLE_STAGES, is_valid_lifecycle_stage, lifecycle_stage_for_index
from src.tile import Tile
from src.world import World, create_world


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_lifecycle_stages_are_valid_and_assigned_by_static_cycle():
    stages = [lifecycle_stage_for_index(index) for index in range(20)]

    assert all(is_valid_lifecycle_stage(stage) for stage in stages)
    assert set(LIFECYCLE_STAGES) == {ADULT, ELDER}
    assert Counter(stages) == {
        ADULT: 16,
        ELDER: 4,
    }


def test_spawned_villagers_receive_lifecycle_stage():
    world = create_world(seed=45, agent_count=20)

    assert all(is_valid_lifecycle_stage(agent.lifecycle_stage) for agent in world.agents)
    assert Counter(agent.lifecycle_stage for agent in world.agents) == {
        ADULT: 16,
        ELDER: 4,
    }


def test_default_agent_lifecycle_stage_is_adult():
    agent = Agent("Ari", 1, 1)

    assert agent.lifecycle_stage == ADULT


def test_some_spawned_villagers_can_be_elders():
    world = create_world(seed=46, agent_count=10)

    assert any(agent.lifecycle_stage == ELDER for agent in world.agents)
    assert any(agent.lifecycle_stage == ADULT for agent in world.agents)


def test_lifecycle_stage_remains_unchanged_during_simulation():
    world = create_world(seed=47, agent_count=10)
    initial_stages = [(agent.name, agent.lifecycle_stage) for agent in world.agents]

    for _ in range(TICKS_PER_DAY * 2):
        world.update()

    assert [(agent.name, agent.lifecycle_stage) for agent in world.agents] == initial_stages


def test_lifecycle_stage_does_not_trigger_death():
    world = make_world()
    elder = Agent("Eli", 2, 2, lifecycle_stage=ELDER)
    world.agents.append(elder)

    for _ in range(5):
        elder.die_if_needed(world)

    assert elder.alive
    assert world.events == []
