import json

from src.death_memory import record_death
from src.diagnostics import diagnostics_sections
from src.births import create_child
from src.families import ensure_family_registry
from src.generations import FAMILY
from src.villager_inspection import villager_detail_sections
from src.world import create_world
from test_births import make_birth_world


def test_starting_villagers_receive_persistent_family_identity():
    world = create_world(seed=2201, agent_count=18)

    ensure_family_registry(world)

    assert world.families
    assert all(agent.family_id for agent in world.agents)
    assert all(agent.family_id in world.families for agent in world.agents)

    agent = world.agents[0]
    original_family_id = agent.family_id
    agent.household_id = "changed-household"
    ensure_family_registry(world)

    assert agent.family_id == original_family_id


def test_child_inherits_family_membership_relationships_and_profile():
    world, parent_a, parent_b = make_birth_world()
    parent_a.trait = "Calm"
    parent_b.trait = "Curious"
    ensure_family_registry(world)

    child = create_child(world, parent_a, parent_b)
    second_child = create_child(world, parent_a, parent_b)
    family = world.families[child.family_id]

    assert child.family_id == parent_a.family_id
    assert child.agent_id in family.living_member_ids
    assert second_child.agent_id in child.sibling_ids
    assert child.agent_id in second_child.sibling_ids
    assert set(child.inheritance_profile.personality_traits) & {"Calm", "Curious", child.trait}
    assert child.inheritance_profile.work_preferences
    json.dumps(family.to_dict())


def test_birth_records_family_memory_and_chronicle_entry():
    world, parent_a, parent_b = make_birth_world()
    ensure_family_registry(world)

    child = create_child(world, parent_a, parent_b)
    family = world.families[child.family_id]

    assert any(child.name in memory.description for memory in family.family_history)
    assert any(entry.category == FAMILY and child.name in entry.description for entry in world.history.entries)


def test_family_diagnostics_and_villager_inspection_expose_identity():
    world = create_world(seed=2202, agent_count=18)
    agent = world.agents[0]

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}
    details = dict(villager_detail_sections(agent, world))

    assert "Families" in sections
    assert sections["Families"]["Families"] >= 1
    assert "Largest Family" in sections["Families"]
    assert ("Family", world.families[agent.family_id].family_name) in details["Identity"]


def test_family_registry_tracks_deceased_members_without_removing_family():
    world = create_world(seed=2203, agent_count=12)
    target = world.agents[0]
    family_id = target.family_id
    family = world.families[family_id]

    record = record_death(world, target, "thirst")

    assert record.family_id == family_id
    assert family_id in world.families
    assert target.agent_id in family.deceased_member_ids
    assert target.agent_id not in family.living_member_ids
    assert any(target.name in memory.description for memory in family.family_history)
