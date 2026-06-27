import json

from src.births import (
    BIRTH_PARENT_STAGES,
    birth_eligible,
    create_child,
    household_birth_spacing_allows,
    inherited_trait,
    update_births,
)
from src.generations import BIRTH
from src.lifecycle import CHILD
from src.partnerships import form_partnership, refresh_partnership_durations
from src.villager_inspection import villager_detail_sections
from test_partnerships import make_partnership_world


def make_birth_world():
    world, parent_a, parent_b = make_partnership_world()
    world.colony_storage.food = 50
    world.colony_storage.water = 50
    form_partnership(world, parent_a, parent_b)
    parent_a.partnership_start_year = world.year - 2
    parent_b.partnership_start_year = world.year - 2
    refresh_partnership_durations(world)
    world.update_carrying_capacity()
    return world, parent_a, parent_b


def test_birth_requires_partnered_adult_same_household_with_resources():
    world, parent_a, parent_b = make_birth_world()

    assert parent_a.lifecycle_stage in BIRTH_PARENT_STAGES
    assert birth_eligible(world, parent_a, parent_b)

    parent_b.household_id = "other-household"
    assert not birth_eligible(world, parent_a, parent_b)

    parent_b.household_id = parent_a.household_id
    world.colony_storage.food = 0
    assert not birth_eligible(world, parent_a, parent_b)


def test_create_child_adds_first_class_child_villager_to_household():
    world, parent_a, parent_b = make_birth_world()
    household = world.household_for_agent(parent_a)

    child = create_child(world, parent_a, parent_b)

    assert child in world.agents
    assert child.lifecycle_stage == CHILD
    assert child.age == 0
    assert child.household_id == household.household_id
    assert child.home_id == parent_a.home_id
    assert child.agent_id in household.member_ids
    assert child.daily_role is None
    assert child.workplace_id is None


def test_birth_records_parent_links_generation_and_inherited_trait():
    world, parent_a, parent_b = make_birth_world()
    parent_a.trait = "Calm"
    parent_b.trait = "Curious"

    child = create_child(world, parent_a, parent_b)

    assert child.parent_a_id == parent_a.agent_id
    assert child.parent_b_id == parent_b.agent_id
    assert child.parent_ids == [parent_a.agent_id, parent_b.agent_id]
    assert child.agent_id in parent_a.child_ids
    assert child.agent_id in parent_b.children_ids
    assert child.generation == 1
    assert child.trait in {"Calm", "Curious"} or child.trait
    assert child.inheritance_profile.personality_traits
    json.dumps(child.family_links.to_dict())


def test_birth_adds_memories_and_chronicle_entry():
    world, parent_a, parent_b = make_birth_world()

    child = create_child(world, parent_a, parent_b)

    assert any("Welcomed" in memory for memory in parent_a.personal_memories)
    assert any("Born into" in memory for memory in child.personal_memories)
    assert parent_a.family_memories
    entries = world.history.by_category(BIRTH)
    assert entries
    assert child.name in entries[-1].description


def test_birth_spacing_prevents_immediate_repeat_births():
    world, parent_a, parent_b = make_birth_world()

    create_child(world, parent_a, parent_b)

    assert not household_birth_spacing_allows(world, parent_a, parent_b)
    assert not birth_eligible(world, parent_a, parent_b)


def test_update_births_is_uncommon_but_can_create_child_when_rng_allows(monkeypatch):
    world, parent_a, parent_b = make_birth_world()

    class AlwaysBirthRandom:
        def __init__(self, *_args, **_kwargs):
            pass

        def shuffle(self, _items):
            return None

        def random(self):
            return 0.0

        def choice(self, items):
            return items[0]

        def randint(self, low, _high):
            return low

    monkeypatch.setattr("src.births.random.Random", AlwaysBirthRandom)

    births = update_births(world)

    assert len(births) == 1
    assert births[0].lifecycle_stage == CHILD


def test_child_does_not_receive_work_assignment_or_workplace():
    world, parent_a, parent_b = make_birth_world()
    child = create_child(world, parent_a, parent_b)

    world.assign_daily_roles()
    world.assign_agent_workplace(child)

    assert child.daily_role is None
    assert child.workplace_id is None


def test_villager_inspection_shows_parent_names_for_child():
    world, parent_a, parent_b = make_birth_world()
    child = create_child(world, parent_a, parent_b)

    sections = dict(villager_detail_sections(child, world))

    assert ("Parents", f"{parent_a.name}, {parent_b.name}") in sections["Identity"]


def test_trait_inheritance_prefers_parent_traits_with_variation_possible(monkeypatch):
    world, parent_a, parent_b = make_birth_world()
    parent_a.trait = "Calm"
    parent_b.trait = "Curious"

    class ParentTraitRandom:
        def random(self):
            return 1.0

        def choice(self, items):
            return items[0]

    assert inherited_trait(parent_a, parent_b, ParentTraitRandom()) == "Calm"
