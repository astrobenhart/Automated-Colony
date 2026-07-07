import random

from src.affection import (
    AFFECTION_ESTABLISHED_THRESHOLD,
    AFFECTION_LIFELONG_THRESHOLD,
    affection_label,
    relationship_grief_penalty,
    relationship_mood_label,
    relationship_positive_mood_bonus,
    update_affection,
)
from src.agent import Agent
from src.death_memory import record_death
from src.diagnostics import derived_mood_score, diagnostics_sections, mood_modifiers
from src.gatherings import gathering_wander_target
from src.partnerships import form_partnership
from src.settlement import Home, Household, Settlement
from src.shared_moments import current_shared_moment, update_shared_moments
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World
from src.world_history import LOCAL_STORY


def make_affection_world() -> tuple[World, Agent, Agent]:
    world = World(12, 12, seed=909)
    world.tiles = [[Tile("grass") for _ in range(12)] for _ in range(12)]
    world.day = 10
    world.season_index = 0
    world.settlement = Settlement(
        "Oakvale",
        6,
        6,
        founded_day=1,
        founded_season="Spring",
        settlement_id="oakvale",
    )
    world.settlement.homes = [Home(6, 6, home_id="home-1", household_id="household-1")]
    world.settlement.households = [
        Household(
            "household-1",
            "Oak Hearth",
            home_id="home-1",
            member_ids=["ari", "bryn"],
            founder_ids=["ari", "bryn"],
            household_head="ari",
            founded_year=1,
            established_years=2,
        )
    ]
    ari = Agent(
        "Ari",
        6,
        6,
        agent_id="ari",
        current_action="Idle",
        home_settlement_id="oakvale",
        household_id="household-1",
        home_id="home-1",
        home_x=6,
        home_y=6,
    )
    bryn = Agent(
        "Bryn",
        7,
        6,
        agent_id="bryn",
        current_action="Idle",
        home_settlement_id="oakvale",
        household_id="household-1",
        home_id="home-1",
        home_x=6,
        home_y=6,
    )
    ari.social_memory["bryn"] = SocialMemoryEntry("bryn", "Bryn", familiarity_score=60, last_seen_day=9)
    bryn.social_memory["ari"] = SocialMemoryEntry("ari", "Ari", familiarity_score=60, last_seen_day=9)
    world.agents = [ari, bryn]
    form_partnership(world, ari, bryn)
    return world, ari, bryn


def test_affection_grows_for_existing_partnerships_over_time():
    world, ari, bryn = make_affection_world()

    for _ in range(5):
        update_affection(world)

    assert ari.partner_affection > 0
    assert ari.partner_affection == bryn.partner_affection
    assert affection_label(ari) == "Growing"


def test_affection_does_not_create_or_change_partnership_formation():
    world = World(8, 8, seed=9)
    world.tiles = [[Tile("grass") for _ in range(8)] for _ in range(8)]
    world.settlement = Settlement("Oakvale", 4, 4, 1, "Spring", settlement_id="oakvale")
    ari = Agent("Ari", 1, 1, agent_id="ari", home_settlement_id="oakvale")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", home_settlement_id="oakvale")
    world.agents = [ari, bryn]

    update_affection(world)

    assert ari.partner_id is None
    assert bryn.partner_id is None
    assert ari.partner_affection == 0
    assert bryn.partner_affection == 0


def test_shared_experiences_increase_affection_more_than_household_only():
    world, ari, bryn = make_affection_world()

    update_affection(world)
    household_only_gain = ari.partner_affection
    ari.partner_affection = 0
    bryn.partner_affection = 0
    update_shared_moments(world)
    assert current_shared_moment(ari, world) is not None

    update_affection(world)

    assert ari.partner_affection > household_only_gain


def test_shared_free_time_modestly_increases_affection():
    world, ari, bryn = make_affection_world()

    update_affection(world)
    free_time_gain = ari.partner_affection
    ari.partner_affection = 0
    bryn.partner_affection = 0
    bryn.current_action = "Building"
    update_affection(world)

    assert free_time_gain > ari.partner_affection


def test_affection_never_overrides_survival_behaviour():
    world, ari, bryn = make_affection_world()
    ari.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    bryn.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    ari.hunger = 90

    update_affection(world)
    target = gathering_wander_target(ari, world, random.Random(1))
    score = derived_mood_score(ari, world)
    positive, negative = mood_modifiers(ari, world)

    assert target is None
    assert score < 80
    assert positive == "Near partner"
    assert negative == "Hunger"


def test_healthy_long_term_partnership_generates_positive_relationship_mood():
    world, ari, bryn = make_affection_world()
    ari.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    bryn.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    baseline = derived_mood_score(ari, world)
    update_shared_moments(world)

    assert relationship_positive_mood_bonus(ari, world) > 0
    assert relationship_mood_label(ari, world) == "Happy"
    assert derived_mood_score(ari, world) > baseline
    positive, negative = mood_modifiers(ari, world)
    assert positive in {"Relationship mood", "Shared moment"}
    assert negative == "None"


def test_lifelong_partners_generate_chronicle_and_inspection_label():
    world, ari, bryn = make_affection_world()
    ari.partner_affection = AFFECTION_LIFELONG_THRESHOLD - 1
    bryn.partner_affection = AFFECTION_LIFELONG_THRESHOLD - 1

    update_affection(world)
    sections = dict(villager_detail_sections(ari, world))

    assert affection_label(ari) == "Lifelong"
    assert ("Relationship", "Lifelong") in sections["Partnership"]
    assert ("Partner Nearby", "Yes") in sections["Partnership"]
    assert ("Relationship Mood", "Happy") in sections["Status"]
    assert any(entry.category == LOCAL_STORY and entry.title == "Lifelong Partnership" for entry in world.history.entries)
    assert any("rarely seen apart" in entry.description for entry in world.history.entries)


def test_partnership_diagnostics_report_shared_free_time():
    world, ari, bryn = make_affection_world()

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert sections["Partnerships"]["Partners Spending Free Time Together"] == 1
    assert sections["Partnerships"]["Partnered Gathering Participation"] == "100.0%"


def test_long_term_partner_loss_creates_grief_and_recovery_without_behavior_override():
    world, ari, bryn = make_affection_world()
    ari.partner_affection = AFFECTION_LIFELONG_THRESHOLD
    bryn.partner_affection = AFFECTION_LIFELONG_THRESHOLD
    bryn.current_action = "Building"

    record_death(world, ari, "old age")

    assert bryn.partner_id is None
    assert bryn.partner_affection == 0
    assert bryn.remembering == "Ari"
    assert bryn.remembrance_expires_day >= world.day + 10
    assert bryn.relationship_grief_until_day > world.day
    assert bryn.relationship_recovery_until_day > bryn.relationship_grief_until_day
    assert relationship_grief_penalty(bryn, world) > 0
    assert relationship_mood_label(bryn, world) == "Grieving"
    assert mood_modifiers(bryn, world)[1] == "Relationship grief"
    assert bryn.current_action == "Building"
    assert any("Mourned lifelong partner Ari" in memory for memory in bryn.personal_memories)
    assert any(entry.category == LOCAL_STORY and entry.title == "Partner Mourned" for entry in world.history.entries)

    world.day = bryn.relationship_grief_until_day
    assert relationship_mood_label(bryn, world) == "Recovering"
    assert relationship_grief_penalty(bryn, world) > 0

    world.day = bryn.relationship_recovery_until_day
    assert relationship_mood_label(bryn, world) == "Content"
    assert relationship_grief_penalty(bryn, world) == 0


def test_relationship_mood_diagnostics_report_positive_and_grief_effects():
    world, ari, bryn = make_affection_world()
    ari.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    bryn.partner_affection = AFFECTION_ESTABLISHED_THRESHOLD
    update_shared_moments(world)
    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}
    assert sections["Mood"]["Positive Relationship Mood Effects"] == 2
    assert sections["Mood"]["Active Grieving Villagers"] == 0
    assert float(sections["Mood"]["Average Relationship Satisfaction"]) > 50

    record_death(world, ari, "old age")
    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}
    assert sections["Mood"]["Active Grieving Villagers"] == 1
