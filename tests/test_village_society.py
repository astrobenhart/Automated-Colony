from src.agent import Agent
from src.celebrations import ActiveCelebration, OPEN_CREMATION
from src.community import (
    COMMUNITY_GROUP_RECOGNITION_COUNT,
    GATHERING_PLACE_RECOGNITION_COUNT,
    TRADITION_RECOGNITION_COUNT,
    community_associations,
    community_diagnostics,
    update_community_recognition,
)
from src.diagnostics import diagnostics_sections
from src.families import Family
from src.roles import BUILDER
from src.settlement import Settlement
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World
from src.world_history import LOCAL_STORY


def make_world(width: int = 12, height: int = 12) -> World:
    world = World(width, height, seed=303)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", 6, 6, 1, "Spring", settlement_id="oakvale")
    return world


def advance_recognition(world: World, days: int):
    for _ in range(days):
        update_community_recognition(world)
        world.day += 1


def test_community_groups_emerge_from_recurring_gatherings():
    world = make_world()
    world.agents = [
        Agent("Ari", 6, 6, agent_id="ari", role=BUILDER, current_action="Idle"),
        Agent("Bryn", 7, 6, agent_id="bryn", role=BUILDER, current_action="Idle"),
        Agent("Cato", 6, 7, agent_id="cato", role=BUILDER, current_action="Idle"),
    ]

    advance_recognition(world, COMMUNITY_GROUP_RECOGNITION_COUNT)

    assert len(world.recognized_community_groups) == 1
    assert world.recognized_community_groups[0].name == "Builder Circle"
    assert any(entry.category == LOCAL_STORY and entry.title == "Community Group" for entry in world.history.entries)


def test_gathering_places_gain_recognition_through_repeated_use():
    world = make_world()
    world.agents = [
        Agent("Ari", 6, 6, agent_id="ari", current_action="Idle"),
        Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle"),
    ]

    advance_recognition(world, GATHERING_PLACE_RECOGNITION_COUNT)

    assert len(world.recognized_gathering_places) == 1
    assert world.recognized_gathering_places[0].name == "Village Centre"
    assert any(entry.category == LOCAL_STORY and entry.title == "Gathering Place" for entry in world.history.entries)


def test_traditions_are_recognised_only_after_repeated_occurrence():
    world = make_world()
    world.celebration_history.append(ActiveCelebration(
        celebration_type=OPEN_CREMATION,
        title="Rowan's Funeral Fire",
        description="A funeral fire was lit for Rowan outside Oakvale.",
        anchor=(2, 2),
        started_day=2,
        duration_days=3,
    ))

    update_community_recognition(world)

    assert world.recognized_traditions == []

    world.celebration_history.append(ActiveCelebration(
        celebration_type=OPEN_CREMATION,
        title="Bryn's Funeral Fire",
        description="A funeral fire was lit for Bryn outside Oakvale.",
        anchor=(3, 2),
        started_day=20,
        duration_days=3,
    ))
    update_community_recognition(world)

    assert len(world.recognized_traditions) == 1
    assert world.recognized_traditions[0].name == "Funeral Fires"
    assert any(entry.category == LOCAL_STORY and entry.title == "Village Tradition" for entry in world.history.entries)


def test_community_recognition_does_not_change_existing_gameplay_state():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", role=BUILDER, current_action="Idle", hunger=12, thirst=8)
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", role=BUILDER, current_action="Idle", hunger=4, thirst=2)
    world.agents = [ari, bryn]
    before = [
        (agent.name, agent.x, agent.y, agent.current_action, agent.current_goal, agent.hunger, agent.thirst, agent.fatigue)
        for agent in world.agents
    ]

    advance_recognition(world, GATHERING_PLACE_RECOGNITION_COUNT)

    after = [
        (agent.name, agent.x, agent.y, agent.current_action, agent.current_goal, agent.hunger, agent.thirst, agent.fatigue)
        for agent in world.agents
    ]
    assert after == before


def test_community_diagnostics_and_inspection_expose_recognised_patterns():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", role=BUILDER, current_action="Idle", family_id="family-ash")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", role=BUILDER, current_action="Idle", family_id="family-ash")
    cato = Agent("Cato", 6, 7, agent_id="cato", role=BUILDER, current_action="Idle", family_id="family-ash")
    world.agents = [ari, bryn, cato]
    world.families["family-ash"] = Family(
        family_id="family-ash",
        family_name="Ash Family",
        generation_count=3,
        living_member_ids=["ari", "bryn", "cato"],
        member_ids=["ari", "bryn", "cato"],
    )
    advance_recognition(world, COMMUNITY_GROUP_RECOGNITION_COUNT)

    rows = dict(community_diagnostics(world))
    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}
    villager_sections = dict(villager_detail_sections(ari, world))
    associations = community_associations(ari, world)

    assert rows["Recognised Community Groups"] == 1
    assert rows["Recognised Gathering Places"] == 1
    assert rows["Oldest Continuing Community Group"] == "Builder Circle"
    assert sections["Living Community"]["Recognised Community Groups"] == 1
    assert "Builder Circle" in associations
    assert "Ash Family" in associations
    assert ("Community Associations", "Builder Circle, Ash Family, Village Centre Regular") in villager_sections["Community"]
