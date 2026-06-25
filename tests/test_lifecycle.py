from collections import Counter

from src.agent import Agent
from src.config import TICKS_PER_DAY
from src.diagnostics import diagnostics_sections
from src.generations import FAMILY
from src.lifecycle import (
    ADULT,
    CHILD,
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
from src.lifecycle_progression import days_until_adulthood, update_lifecycle_progression
from src.roles import GENERALIST
from src.social_memory import villager_key
from src.task_behavior import assign_daily_role, run_villager_task
from src.tile import Tile
from src.world import World, create_world


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def add_child_to_world(world: World, age: int = 5, *, turning_adult: bool = False) -> Agent:
    parent = world.agents[0]
    household = world.household_for_agent(parent)
    birth_year = world.year - (18 if turning_adult else age)
    child = Agent(
        "Lio",
        parent.x,
        parent.y,
        role=GENERALIST,
        lifecycle_stage=CHILD,
        age=age,
        experience_level="Novice",
        trait=parent.trait,
        agent_id=f"test-child-{len(world.agents)}",
        household_id=getattr(parent, "household_id", None),
        home_id=getattr(parent, "home_id", None),
        home_x=getattr(parent, "home_x", None),
        home_y=getattr(parent, "home_y", None),
        home_settlement_id=getattr(parent, "home_settlement_id", None),
        birth_settlement_id=getattr(parent, "birth_settlement_id", None),
        birth_year=birth_year,
        birth_day=world.day_of_year,
        parent_a_id=villager_key(parent),
        parent_ids=[villager_key(parent)],
        generation=1,
        current_action="At home",
        current_goal="Grow",
        daily_role=None,
    )
    world.agents.append(child)
    if household is not None:
        world.add_agent_to_household(child, household)
    return child


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


def test_existing_starting_adults_do_not_age_within_two_days():
    world = create_world(seed=47, agent_count=10)
    initial_stages = [(agent.name, agent.lifecycle_stage) for agent in world.agents]
    initial_ages = [(agent.name, agent.age) for agent in world.agents]

    for _ in range(TICKS_PER_DAY * 2):
        world.update()

    assert [(agent.name, agent.lifecycle_stage) for agent in world.agents] == initial_stages
    assert [(agent.name, agent.age) for agent in world.agents] == initial_ages


def test_child_is_dependent_and_does_not_receive_work_assignment():
    world = create_world(seed=147, agent_count=6)
    child = add_child_to_world(world, age=5)
    child.daily_role = "food"

    assign_daily_role(child, world)
    run_villager_task(child, world)

    assert child.lifecycle_stage == CHILD
    assert child.daily_role is None
    assert child.current_action == "At home"
    assert child.current_goal == "Grow"


def test_child_ages_into_workforce_eligible_adult_stage():
    world = create_world(seed=148, agent_count=6)
    parent = world.agents[0]
    household = world.household_for_agent(parent)
    child = add_child_to_world(world, age=17, turning_adult=True)
    original_trait = child.trait
    original_household_id = child.household_id

    transitions = update_lifecycle_progression(world)

    assert len(transitions) == 1
    assert child.age == 18
    assert child.lifecycle_stage == YOUNG_ADULT
    assert child.role == GENERALIST
    assert child.trait == original_trait
    assert child.household_id == original_household_id
    assert household is not None and villager_key(child) in household.member_ids
    assert world.adults_this_year[world.year] == 1
    assert any("Reached adulthood" in memory for memory in child.personal_memories)
    assert any("reached adulthood" in memory for memory in parent.personal_memories)
    assert any(entry.category == FAMILY and child.name in entry.description for entry in world.history.entries)


def test_lifecycle_diagnostics_report_children_and_transitions():
    world = create_world(seed=149, agent_count=6)
    child = add_child_to_world(world, age=17, turning_adult=True)

    section_map = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert section_map["Children"]["Total Children"] == 1
    assert section_map["Children"]["Oldest Child"] == 17
    assert section_map["Children"]["Upcoming Adult Transitions"] == 1
    assert section_map["Adults"]["Total Adults"] == len(world.living_agents()) - 1
    assert section_map["Lifecycle"]["Adults This Year"] == 0
    assert days_until_adulthood(world, child) == 0


def test_lifecycle_stage_does_not_trigger_death():
    world = make_world()
    elder = Agent("Eli", 2, 2, lifecycle_stage=ELDER)
    world.agents.append(elder)

    for _ in range(5):
        elder.die_if_needed(world)

    assert elder.alive
    assert world.events == []
