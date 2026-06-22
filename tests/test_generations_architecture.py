import json

from src.agent import Agent
from src.death_memory import record_death
from src.generations import (
    BIRTH,
    FAMILY,
    FUTURE_DEATH_CAUSES,
    FUTURE_FAMILY_MEMORY_CATEGORIES,
    FUTURE_LIFE_STAGES,
    FUTURE_RELATIONSHIP_TYPES,
    HouseholdLineageRecord,
    InheritanceProfile,
    LifecycleRecord,
    SUCCESSION,
)
from src.lifecycle import CHILD, LIFECYCLE_STAGES, is_valid_lifecycle_stage
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.world import World, create_world
from src.world_history import HISTORY_CATEGORIES


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_villagers_have_future_family_and_lifecycle_fields_without_generated_family():
    world = create_world(seed=501, agent_count=30)

    assert all(agent.birth_year is not None for agent in world.agents)
    assert all(agent.death_year is None for agent in world.agents)
    assert all(agent.mother_id is None for agent in world.agents)
    assert all(agent.father_id is None for agent in world.agents)
    assert all(agent.parent_ids == [] for agent in world.agents)
    assert all(agent.child_ids == [] for agent in world.agents)
    assert all(agent.children_ids == [] for agent in world.agents)
    assert all(agent.sibling_ids == [] for agent in world.agents)
    assert all(agent.partner_ids == [] for agent in world.agents)


def test_child_stage_is_supported_but_not_generated_at_startup():
    world = create_world(seed=502, agent_count=45)

    assert CHILD in FUTURE_LIFE_STAGES
    assert CHILD not in LIFECYCLE_STAGES
    assert is_valid_lifecycle_stage(CHILD)
    assert all(agent.lifecycle_stage != CHILD for agent in world.agents)


def test_agent_family_links_sync_parent_child_aliases():
    agent = Agent(
        "Ari",
        1,
        1,
        mother_id="mara",
        father_id="elric",
        child_ids=["rowan"],
        sibling_ids=["tessa"],
    )

    assert agent.parent_ids == ["mara", "elric"]
    assert agent.children_ids == ["rowan"]
    assert agent.family_links.to_dict() == {
        "mother_id": "mara",
        "father_id": "elric",
        "parent_ids": ["mara", "elric"],
        "children_ids": ["rowan"],
        "sibling_ids": ["tessa"],
        "partner_ids": [],
    }


def test_households_have_lineage_fields_for_future_generations():
    world = create_world(seed=503, agent_count=30)
    household = world.settlement.households[0]

    assert household.generation_count >= 1
    assert household.historical_member_ids
    assert set(household.member_ids) <= set(household.historical_member_ids)
    record = HouseholdLineageRecord(
        household_id=household.household_id,
        founder_ids=household.founder_ids,
        generation_count=household.generation_count,
        historical_member_ids=household.historical_member_ids,
    )
    json.dumps(record.to_dict())


def test_inheritance_profile_mirrors_existing_identity_without_inheritance_logic():
    agent = Agent("Ari", 1, 1, trait="Curious", role="Builder", appearance_seed=42, appearance_type="Round")

    profile = agent.inheritance_profile

    assert profile.personality_traits == ["Curious"]
    assert profile.work_preferences == ["Builder"]
    assert profile.appearance_traits == {
        "appearance_seed": 42,
        "appearance_type": "Round",
    }
    json.dumps(profile.to_dict())


def test_future_family_memory_relationship_and_death_categories_exist():
    assert {"parent", "child", "sibling", "partner"} <= set(FUTURE_RELATIONSHIP_TYPES)
    assert {"parent", "child", "sibling", "family_loss"} <= set(FUTURE_FAMILY_MEMORY_CATEGORIES)
    assert {"old_age", "illness", "accident", "mysterious_event"} <= set(FUTURE_DEATH_CAUSES)
    assert {BIRTH, FAMILY, SUCCESSION} <= HISTORY_CATEGORIES


def test_social_memory_can_carry_future_relationship_type_tags():
    entry = SocialMemoryEntry(
        "mara",
        "Mara",
        familiarity_score=30,
        last_seen_day=2,
        relationship_types=["parent"],
    )

    assert entry.relationship_types == ["parent"]


def test_death_record_preserves_generation_architecture_fields():
    world = make_world()
    agent = Agent(
        "Rowan",
        1,
        1,
        agent_id="rowan",
        birth_year=-31,
        mother_id="mara",
        father_id="elric",
        sibling_ids=["tessa"],
        household_id="household-1",
        home_id="home-1",
        generation=2,
    )
    world.agents = [agent]

    record = record_death(world, agent, "starvation")

    assert agent.death_year == world.year
    assert record.birth_year == -31
    assert record.death_year == world.year
    assert record.mother_id == "mara"
    assert record.father_id == "elric"
    assert record.parent_ids == ["mara", "elric"]
    assert record.sibling_ids == ["tessa"]
    assert record.household_id == "household-1"
    assert record.home_id == "home-1"
    assert record.generation == 2


def test_generation_architecture_records_are_json_safe():
    lifecycle = LifecycleRecord(
        birth_year=1,
        birth_day=12,
        life_stage_history=[(1, "Child"), (18, "Young Adult")],
    )
    inheritance = InheritanceProfile(
        personality_traits=["Calm"],
        work_preferences=["Forager"],
        social_tendencies=["Friendly"],
        appearance_traits={"hair": "dark"},
    )

    json.dumps(lifecycle.to_dict())
    json.dumps(inheritance.to_dict())
