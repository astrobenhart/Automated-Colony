import random

from src.agent import Agent
from src.diagnostics import diagnostics_sections
from src.friendships import CLOSE_FRIEND_THRESHOLD, record_friendship_interaction
from src.gatherings import (
    active_gatherings,
    gathering_diagnostics,
    gathering_wander_target,
    social_state,
)
from src.settlement import Home, Household, Settlement
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World


def make_world(width: int = 14, height: int = 14) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", 7, 7, 1, "Spring", settlement_id="oakvale")
    return world


def test_idle_villager_naturally_targets_existing_gathering():
    world = make_world()
    ari = Agent("Ari", 2, 2, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 7, agent_id="bryn", current_action="Idle")
    cato = Agent("Cato", 8, 7, agent_id="cato", current_action="Idle")
    world.agents = [ari, bryn, cato]

    target = gathering_wander_target(ari, world, random.Random(4))

    assert target is not None
    assert max(abs(target[0] - 7), abs(target[1] - 7)) <= 1


def test_close_friends_prefer_gathering_near_each_other():
    world = make_world()
    ari = Agent("Ari", 2, 2, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 11, 11, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]
    record_friendship_interaction(world, ari, bryn, CLOSE_FRIEND_THRESHOLD)

    target = gathering_wander_target(ari, world, random.Random(7))

    assert target is not None
    assert max(abs(target[0] - bryn.x), abs(target[1] - bryn.y)) <= 1


def test_family_members_naturally_remain_close_during_free_time():
    world = make_world()
    child = Agent("Ari", 2, 2, agent_id="ari", lifecycle_stage="Child", family_id="family-1", current_action="Idle")
    parent = Agent("Bryn", 10, 10, agent_id="bryn", family_id="family-1", current_action="Idle")
    world.agents = [child, parent]

    target = gathering_wander_target(child, world, random.Random(9))

    assert target is not None
    assert max(abs(target[0] - parent.x), abs(target[1] - parent.y)) <= 1


def test_gatherings_never_interrupt_survival_needs():
    world = make_world()
    ari = Agent("Ari", 2, 2, agent_id="ari", current_action="Idle", hunger=90)
    bryn = Agent("Bryn", 7, 7, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]

    assert gathering_wander_target(ari, world, random.Random(1)) is None


def test_multiple_gatherings_emerge_from_separate_idle_clusters():
    world = make_world()
    world.agents = [
        Agent("Ari", 2, 2, agent_id="ari", current_action="Idle"),
        Agent("Bryn", 3, 2, agent_id="bryn", current_action="Idle"),
        Agent("Cato", 2, 3, agent_id="cato", current_action="Idle"),
        Agent("Dara", 10, 10, agent_id="dara", current_action="Idle"),
        Agent("Eli", 11, 10, agent_id="eli", current_action="Idle"),
        Agent("Fenn", 10, 11, agent_id="fenn", current_action="Idle"),
    ]

    clusters = active_gatherings(world)

    assert len(clusters) == 2
    assert sorted(cluster.size for cluster in clusters) == [3, 3]


def test_working_villagers_are_not_counted_as_gathering_participants():
    world = make_world()
    world.agents = [
        Agent("Ari", 7, 7, agent_id="ari", current_action="Building"),
        Agent("Bryn", 8, 7, agent_id="bryn", current_action="Idle"),
        Agent("Cato", 8, 8, agent_id="cato", current_action="Idle"),
    ]

    clusters = active_gatherings(world)

    assert len(clusters) == 1
    assert clusters[0].size == 2


def test_gathering_diagnostics_report_active_groups_and_destinations():
    world = make_world()
    world.agents = [
        Agent("Ari", 7, 7, agent_id="ari", current_action="Idle"),
        Agent("Bryn", 8, 7, agent_id="bryn", current_action="Idle"),
    ]

    rows = dict(gathering_diagnostics(world))

    assert rows["Active Gatherings"] == 1
    assert rows["Largest Gathering"] == 2
    assert rows["Idle Villagers Participating"] == 2
    assert "Village Centre" in rows["Gathering Destinations"]


def test_diagnostics_include_gathering_section():
    world = make_world()
    world.agents = [
        Agent("Ari", 7, 7, agent_id="ari", current_action="Idle"),
        Agent("Bryn", 8, 7, agent_id="bryn", current_action="Idle"),
    ]

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert sections["Gatherings"]["Active Gatherings"] == 1


def test_villager_inspection_exposes_compact_social_state():
    world = make_world()
    ari = Agent("Ari", 7, 7, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 8, 7, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]

    sections = dict(villager_detail_sections(ari, world))

    assert ("Social", "Gathering") in sections["Status"]
    assert social_state(ari, world) == "Gathering"


def test_household_destination_supports_visiting_without_new_gathering_places():
    world = make_world()
    world.settlement.homes = [Home(10, 10, home_id="home-1", household_id="household-1")]
    world.settlement.households = [
        Household("household-1", "Bryn Household", home_id="home-1", member_ids=["bryn"])
    ]
    ari = Agent("Ari", 2, 2, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 10, 10, agent_id="bryn", current_action="Idle", household_id="household-1", home_id="home-1")
    world.agents = [ari, bryn]
    record_friendship_interaction(world, ari, bryn, CLOSE_FRIEND_THRESHOLD)

    target = gathering_wander_target(ari, world, random.Random(3))

    assert target is not None
    assert max(abs(target[0] - 10), abs(target[1] - 10)) <= 1
