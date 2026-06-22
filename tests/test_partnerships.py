import json

from src.agent import Agent
from src.generations import FAMILY, RELATIONSHIP_PARTNER
from src.partnerships import (
    PARTNER_FAMILIARITY_FLOOR,
    form_partnership,
    partnership_eligible,
    partnership_score,
    refresh_partnership_durations,
)
from src.settlement import Home, Household, Settlement
from src.social_memory import SocialMemoryEntry, relationship_summary
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World


def make_partnership_world() -> tuple[World, Agent, Agent]:
    world = World(8, 8, seed=902)
    world.tiles = [[Tile("grass") for _ in range(8)] for _ in range(8)]
    world.day = 30
    world.season_index = 0
    world.settlement = Settlement(
        "Test Village",
        4,
        4,
        founded_day=1,
        founded_season="Spring",
        settlement_id="settlement-1",
    )
    first_home = Home(2, 2, home_id="home-1", household_id="household-1")
    second_home = Home(5, 5, home_id="home-2", household_id="household-2")
    first_household = Household(
        "household-1",
        "Oak Hearth",
        home_id="home-1",
        member_ids=["ari"],
        founder_ids=["ari"],
        household_head="ari",
        founded_year=10,
        established_years=2,
    )
    second_household = Household(
        "household-2",
        "Willow Hearth",
        home_id="home-2",
        member_ids=["bryn"],
        founder_ids=["bryn"],
        household_head="bryn",
        founded_year=10,
        established_years=2,
    )
    world.settlement.homes = [first_home, second_home]
    world.settlement.households = [first_household, second_household]
    ari = Agent(
        "Ari",
        2,
        2,
        agent_id="ari",
        home_settlement_id="settlement-1",
        household_id="household-1",
        home_id="home-1",
        home_x=2,
        home_y=2,
    )
    bryn = Agent(
        "Bryn",
        5,
        5,
        agent_id="bryn",
        home_settlement_id="settlement-1",
        household_id="household-2",
        home_id="home-2",
        home_x=5,
        home_y=5,
    )
    ari.social_memory["bryn"] = SocialMemoryEntry("bryn", "Bryn", familiarity_score=58, last_seen_day=29)
    bryn.social_memory["ari"] = SocialMemoryEntry("ari", "Ari", familiarity_score=56, last_seen_day=29)
    world.agents = [ari, bryn]
    return world, ari, bryn


def test_partnership_forms_from_strong_existing_social_bond():
    world, ari, bryn = make_partnership_world()

    form_partnership(world, ari, bryn)

    assert ari.partner_id == "bryn"
    assert bryn.partner_id == "ari"
    assert ari.partnership_start_year == world.year
    assert bryn.partnership_start_year == world.year
    assert ari.partner_ids == ["bryn"]
    assert bryn.family_links.partner_ids == ["ari"]
    json.dumps(ari.family_links.to_dict())


def test_partnership_eligibility_excludes_direct_family_and_existing_partners():
    world, ari, bryn = make_partnership_world()

    assert partnership_eligible(ari, bryn, world)

    ari.child_ids = ["bryn"]
    assert not partnership_eligible(ari, bryn, world)

    ari.child_ids = []
    ari.partner_id = "other"
    assert not partnership_eligible(ari, bryn, world)


def test_partnership_score_uses_social_household_and_workplace_history():
    world, ari, bryn = make_partnership_world()
    ari.workplace_id = "farm-1"
    bryn.workplace_id = "farm-1"

    assert partnership_score(ari, bryn, world) >= 60


def test_partners_prefer_shared_household_without_duplicate_membership():
    world, ari, bryn = make_partnership_world()

    form_partnership(world, ari, bryn)

    assert ari.household_id == "household-2"
    assert bryn.household_id == "household-2"
    memberships = [
        household.household_id
        for household in world.settlement.households
        if "ari" in household.member_ids
    ]
    assert memberships == ["household-2"]
    assert ari.home_id == "home-2"


def test_partner_relationship_type_memory_and_chronicle_are_recorded():
    world, ari, bryn = make_partnership_world()

    form_partnership(world, ari, bryn)

    entry = ari.social_memory["bryn"]
    assert entry.familiarity_score >= PARTNER_FAMILIARITY_FLOOR
    assert RELATIONSHIP_PARTNER in entry.relationship_types
    assert ("Partner", "Bryn") in relationship_summary(ari)
    assert any("long-term partnership" in memory for memory in ari.personal_memories)
    assert world.history.by_category(FAMILY)


def test_partnership_duration_refreshes_from_start_year():
    world, ari, bryn = make_partnership_world()
    form_partnership(world, ari, bryn)
    ari.partnership_start_year = world.year - 3
    bryn.partnership_start_year = world.year - 3

    refresh_partnership_durations(world)

    assert ari.partnership_duration == 3
    assert bryn.partnership_duration == 3


def test_villager_inspection_shows_partner_compactly():
    world, ari, bryn = make_partnership_world()
    form_partnership(world, ari, bryn)

    sections = dict(villager_detail_sections(ari, world))

    assert ("Partner", "Bryn") in sections["Partnership"]
    assert ("Partnership", "0 years") in sections["Partnership"]
