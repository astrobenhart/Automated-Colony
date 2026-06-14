from src.agent import Agent
from src.social_memory import (
    ACQUAINTED,
    FAMILIAR,
    SEEN,
    STRANGER,
    SocialMemoryEntry,
    familiarity_level,
    familiarity_summary,
    record_observation,
    update_social_memory,
)
from src.tile import Tile
from src.world import World


def make_world(width: int = 10, height: int = 10) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_familiarity_starts_empty():
    agent = Agent("Ari", 1, 1)

    assert agent.social_memory == {}


def test_near_villagers_gain_familiarity():
    world = make_world()
    world.day = 5
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 3, 1, agent_id="bryn")
    world.agents = [ari, bryn]

    update_social_memory(world, radius=4)

    assert ari.social_memory["bryn"].familiarity_score == 1
    assert ari.social_memory["bryn"].last_seen_day == 5
    assert bryn.social_memory["ari"].familiarity_score == 1
    assert bryn.social_memory["ari"].last_seen_day == 5


def test_far_villagers_do_not_gain_familiarity():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 8, 8, agent_id="bryn")
    world.agents = [ari, bryn]

    update_social_memory(world, radius=4)

    assert ari.social_memory == {}
    assert bryn.social_memory == {}


def test_repeated_observations_increase_familiarity_slowly():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]

    for day in range(1, 4):
        world.day = day
        update_social_memory(world, radius=4)

    entry = ari.social_memory["bryn"]
    assert entry.familiarity_score == 3
    assert entry.last_seen_day == 3
    assert familiarity_level(entry.familiarity_score) == SEEN


def test_familiarity_thresholds_are_neutral_and_slow():
    assert familiarity_level(0) == STRANGER
    assert familiarity_level(1) == STRANGER
    assert familiarity_level(2) == SEEN
    assert familiarity_level(9) == SEEN
    assert familiarity_level(10) == ACQUAINTED
    assert familiarity_level(29) == ACQUAINTED
    assert familiarity_level(30) == FAMILIAR


def test_familiarity_summary_shows_top_three_non_strangers():
    ari = Agent("Ari", 1, 1)
    ari.social_memory = {
        "bryn": SocialMemoryEntry("bryn", "Bryn", familiarity_score=30, last_seen_day=30),
        "cato": SocialMemoryEntry("cato", "Cato", familiarity_score=10, last_seen_day=30),
        "dara": SocialMemoryEntry("dara", "Dara", familiarity_score=2, last_seen_day=30),
        "eli": SocialMemoryEntry("eli", "Eli", familiarity_score=1, last_seen_day=30),
        "fenn": SocialMemoryEntry("fenn", "Fenn", familiarity_score=12, last_seen_day=30),
    }

    assert familiarity_summary(ari) == [
        "Bryn (Familiar)",
        "Fenn (Acquainted)",
        "Cato (Acquainted)",
    ]


def test_dead_villagers_are_ignored_safely():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", alive=False)
    world.agents = [ari, bryn]

    update_social_memory(world, radius=4)

    assert ari.social_memory == {}
    assert bryn.social_memory == {}


def test_last_seen_day_updates_after_later_observation():
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")

    record_observation(ari, bryn, day=2)
    record_observation(ari, bryn, day=9)

    assert ari.social_memory["bryn"].familiarity_score == 2
    assert ari.social_memory["bryn"].last_seen_day == 9


def test_social_memory_has_no_gameplay_effects():
    world = make_world()
    ari = Agent("Ari", 1, 1, current_goal="Explore", current_action="Idle", hunger=10, thirst=10)
    bryn = Agent("Bryn", 2, 1)
    world.agents = [ari, bryn]
    before = (
        ari.current_goal,
        ari.current_action,
        ari.hunger,
        ari.thirst,
        ari.fatigue,
        ari.role,
        ari.lifecycle_stage,
        ari.trait,
    )

    update_social_memory(world, radius=4)

    assert (
        ari.current_goal,
        ari.current_action,
        ari.hunger,
        ari.thirst,
        ari.fatigue,
        ari.role,
        ari.lifecycle_stage,
        ari.trait,
    ) == before
