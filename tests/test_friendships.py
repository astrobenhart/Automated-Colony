from src.agent import Agent
from src.death_memory import record_death
from src.diagnostics import diagnostics_sections, derived_mood_score, mood_modifiers
from src.friendships import (
    CLOSE_FRIEND_THRESHOLD,
    KNOWN_FRIEND_LIMIT,
    FriendshipEntry,
    friendship_displays,
    record_friendship_interaction,
    update_friendships,
)
from src.settlement import Household, Settlement
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.workplace import FARM, Workplace
from src.world import World
from src.world_history import LOCAL_STORY


def make_world(width: int = 12, height: int = 12) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", 5, 5, 1, "Spring", settlement_id="oakvale")
    return world


def test_friendship_formation_and_strengthening_records_meaningful_story():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]

    for _ in range(CLOSE_FRIEND_THRESHOLD):
        record_friendship_interaction(world, ari, bryn)

    assert ari.friendships["bryn"].score == CLOSE_FRIEND_THRESHOLD
    assert bryn.friendships["ari"].score == CLOSE_FRIEND_THRESHOLD
    assert world.friendship_formations_by_year[world.year] == 1
    assert any(entry.category == LOCAL_STORY and "became close friends" in entry.description for entry in world.history.entries)


def test_friendship_memory_is_capped_to_meaningful_friends():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    others = [Agent(f"Friend{i}", i + 2, 1, agent_id=f"friend-{i}") for i in range(8)]
    world.agents = [ari, *others]

    for index, other in enumerate(others):
        for _ in range(index + 1):
            record_friendship_interaction(world, ari, other)

    update_friendships(world)

    assert len(ari.friendships) == KNOWN_FRIEND_LIMIT
    assert "friend-7" in ari.friendships
    assert "friend-0" not in ari.friendships


def test_household_friendship_forms_from_daily_social_update():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari", household_id="household-1")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", household_id="household-1")
    world.agents = [ari, bryn]
    world.settlement.households = [
        Household("household-1", "Ari Household", member_ids=["ari", "bryn"])
    ]

    update_friendships(world)

    assert ari.friendships["bryn"].score >= 3
    assert bryn.friendships["ari"].score >= 3


def test_workplace_friendship_forms_from_daily_social_update():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 8, 8, agent_id="bryn")
    world.agents = [ari, bryn]
    world.settlement.workplaces = [
        Workplace("farm-0", FARM, 5, 5, 4, assigned_workers=["ari", "bryn"])
    ]

    update_friendships(world)

    assert ari.friendships["bryn"].score >= 2
    assert bryn.friendships["ari"].score >= 2


def test_friendship_survives_normal_gameplay_daily_update():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari", household_id="household-1")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", household_id="household-1")
    world.agents = [ari, bryn]
    world.settlement.households = [
        Household("household-1", "Ari Household", member_ids=["ari", "bryn"])
    ]

    world.run_daily_updates()

    assert ari.friendships["bryn"].score > 0
    assert bryn.friendships["ari"].score > 0


def test_villager_inspection_displays_friendship_strength():
    agent = Agent("Ari", 1, 1, agent_id="ari")
    agent.friendships["bryn"] = FriendshipEntry("bryn", "Bryn", score=56)

    sections = {section: rows for section, rows in villager_detail_sections(agent)}

    assert ("Best Friend", "Bryn (56)") in sections["Friends"]


def test_friendship_diagnostics_report_social_debug_values():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]
    record_friendship_interaction(world, ari, bryn, CLOSE_FRIEND_THRESHOLD)

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert sections["Friendships"]["Close Friendships"] == 1
    assert sections["Friendships"]["Most Connected Villager"] in {"Ari", "Bryn"}


def test_close_friend_death_removes_active_friendship_and_applies_mourning():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]
    record_friendship_interaction(world, ari, bryn, CLOSE_FRIEND_THRESHOLD)

    record_death(world, bryn, "old age")

    assert "bryn" not in ari.friendships
    assert ari.remembering == "Bryn"
    assert any("Mourned close friend Bryn" in memory for memory in ari.personal_memories)
    assert world.friendship_losses_by_year[world.year] == 1
    assert any(entry.category == LOCAL_STORY and entry.title == "Friend Mourned" for entry in world.history.entries)


def test_friendship_mood_effects_are_subtle_and_survival_still_dominates():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari", hunger=90)
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]
    record_friendship_interaction(world, ari, bryn, CLOSE_FRIEND_THRESHOLD)

    score = derived_mood_score(ari, world)
    positive, negative = mood_modifiers(ari, world)

    assert score < 80
    assert positive == "Near close friend"
    assert negative == "Hunger"


def test_friendship_display_uses_compact_friend_labels():
    agent = Agent("Ari", 1, 1, agent_id="ari")
    agent.friendships["bryn"] = FriendshipEntry("bryn", "Bryn", score=35)
    agent.friendships["cato"] = FriendshipEntry("cato", "Cato", score=58)

    displays = friendship_displays(agent)

    assert [(display.label, display.name, display.strength) for display in displays] == [
        ("Best Friend", "Cato", 58),
        ("Close Friend", "Bryn", 35),
    ]
