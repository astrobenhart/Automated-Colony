from collections import Counter

from src.agent import Agent
from src.config import TICKS_PER_DAY
from src.lifecycle import (
    ADULT,
    ELDER,
    EXPERIENCED,
    EXPERIENCE_LEVELS,
    LIFECYCLE_STAGES,
    OLDER_ADULT,
    VETERAN,
    YOUNG_ADULT,
    demographic_profiles,
    is_valid_experience_level,
    is_valid_lifecycle_stage,
    lifecycle_stage_for_age,
    lifecycle_stage_for_index,
)
from src.tile import Tile
from src.world import World, create_world


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_lifecycle_stages_include_starting_adult_demographics():
    profiles = demographic_profiles(60, seed=12)
    stages = [profile.lifecycle_stage for profile in profiles]
    counts = Counter(stages)

    assert all(is_valid_lifecycle_stage(stage) for stage in stages)
    assert set(LIFECYCLE_STAGES) == {YOUNG_ADULT, ADULT, OLDER_ADULT, ELDER}
    assert 12 <= counts[YOUNG_ADULT] <= 18
    assert 30 <= counts[ADULT] <= 36
    assert 9 <= counts[OLDER_ADULT] <= 13
    assert 1 <= counts[ELDER] <= 4


def test_spawned_villagers_receive_lifecycle_stage():
    world = create_world(seed=45, agent_count=45)
    counts = Counter(agent.lifecycle_stage for agent in world.agents)

    assert all(is_valid_lifecycle_stage(agent.lifecycle_stage) for agent in world.agents)
    assert counts[YOUNG_ADULT] > 0
    assert counts[ADULT] > counts[ELDER]
    assert counts[OLDER_ADULT] > 0
    assert counts[ELDER] > 0


def test_spawned_villagers_receive_age_and_experience():
    world = create_world(seed=48, agent_count=45)

    assert all(agent.age >= 18 for agent in world.agents)
    assert all(lifecycle_stage_for_age(agent.age) == agent.lifecycle_stage for agent in world.agents)
    assert all(is_valid_experience_level(agent.experience_level) for agent in world.agents)
    assert {agent.experience_level for agent in world.agents} >= {EXPERIENCED, VETERAN}


def test_default_agent_lifecycle_stage_is_adult():
    agent = Agent("Ari", 1, 1)

    assert agent.lifecycle_stage == ADULT
    assert agent.age == 35
    assert agent.experience_level == EXPERIENCED


def test_some_spawned_villagers_can_be_elders():
    world = create_world(seed=46, agent_count=10)

    assert any(agent.lifecycle_stage == ELDER for agent in world.agents)
    assert any(agent.lifecycle_stage == ADULT for agent in world.agents)


def test_lifecycle_stage_remains_unchanged_during_simulation():
    world = create_world(seed=47, agent_count=10)
    initial_stages = [(agent.name, agent.lifecycle_stage) for agent in world.agents]
    initial_ages = [(agent.name, agent.age) for agent in world.agents]

    for _ in range(TICKS_PER_DAY * 2):
        world.update()

    assert [(agent.name, agent.lifecycle_stage) for agent in world.agents] == initial_stages
    assert [(agent.name, agent.age) for agent in world.agents] == initial_ages


def test_lifecycle_stage_does_not_trigger_death():
    world = make_world()
    elder = Agent("Eli", 2, 2, lifecycle_stage=ELDER)
    world.agents.append(elder)

    for _ in range(5):
        elder.die_if_needed(world)

    assert elder.alive
    assert world.events == []
