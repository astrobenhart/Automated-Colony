from src.agent import Agent
from src.config import HUNGER_DEATH_THRESHOLD
from src.death_memory import (
    REMEMBRANCE_DURATION_DAYS,
    active_remembrance_name,
    death_history_description,
    expire_remembrances,
    record_death,
)
from src.lifecycle import ELDER
from src.roles import BUILDER, FORAGER
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World
from src.world_history import DEATH


def make_world(width: int = 8, height: int = 8) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def remember(observer: Agent, target: Agent, score: int, day: int):
    key = target.agent_id or target.name
    observer.social_memory[key] = SocialMemoryEntry(
        villager_id=key,
        display_name=target.name,
        familiarity_score=score,
        last_seen_day=day,
    )


def test_death_record_preserves_identity_cause_and_date():
    world = make_world()
    world.day = 18
    world.season_index = 2
    target = Agent(
        "Rowan",
        1,
        1,
        agent_id="rowan",
        role=BUILDER,
        lifecycle_stage=ELDER,
        trait="Stubborn",
        appearance_seed=42,
        appearance_type="Round",
    )
    world.agents = [target]

    record = record_death(world, target, "thirst")

    assert record.name == "Rowan"
    assert record.villager_id == "rowan"
    assert record.role == BUILDER
    assert record.lifecycle_stage == ELDER
    assert record.trait == "Stubborn"
    assert record.appearance_seed == 42
    assert record.appearance_type == "Round"
    assert record.cause_of_death == "thirst"
    assert record.day == 18
    assert record.season == "Autumn"
    assert record.year == world.year


def test_death_record_captures_influence_and_peak_influence_labels():
    world = make_world()
    world.day = 12
    target = Agent("Rowan", 1, 1, agent_id="rowan", peak_influence_score=24)
    observer = Agent("Ari", 2, 1, agent_id="ari")
    remember(observer, target, score=30, day=12)
    world.agents = [target, observer]

    record = record_death(world, target, "starvation")

    assert record.influence_label == "Emerging"
    assert record.peak_influence_label == "Respected"


def test_familiar_villagers_are_remembered_but_strangers_are_not():
    world = make_world()
    world.day = 20
    target = Agent("Rowan", 1, 1, agent_id="rowan")
    familiar = Agent("Ari", 2, 1, agent_id="ari")
    stranger = Agent("Bryn", 3, 1, agent_id="bryn")
    seen_once = Agent("Cato", 4, 1, agent_id="cato")
    remember(familiar, target, score=30, day=20)
    remember(seen_once, target, score=2, day=20)
    world.agents = [target, familiar, stranger, seen_once]

    record = record_death(world, target, "thirst")

    assert record.remembered_by == ["Ari"]
    assert active_remembrance_name(familiar, world) == "Rowan"
    assert active_remembrance_name(stranger, world) is None
    assert active_remembrance_name(seen_once, world) is None


def test_death_record_handles_missing_social_memory_safely():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan")
    observer = Agent("Ari", 2, 1, agent_id="ari")
    observer.social_memory = {}
    world.agents = [target, observer]

    record = record_death(world, target, "thirst")

    assert record.remembered_by == []


def test_death_record_is_not_duplicated():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan")
    world.agents = [target]

    first = record_death(world, target, "thirst")
    second = record_death(world, target, "starvation")

    assert first is second
    assert len(world.death_records) == 1
    assert world.history.count() == 1


def test_remembrance_expires_after_duration():
    world = make_world()
    world.day = 5
    target = Agent("Rowan", 1, 1, agent_id="rowan")
    observer = Agent("Ari", 2, 1, agent_id="ari")
    remember(observer, target, score=30, day=5)
    world.agents = [target, observer]

    record_death(world, target, "thirst")

    assert observer.remembrance_expires_day == 5 + REMEMBRANCE_DURATION_DAYS
    world.day = observer.remembrance_expires_day
    expire_remembrances(world)

    assert active_remembrance_name(observer, world) is None
    assert observer.remembering is None


def test_agent_death_path_creates_single_death_record():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan", hunger=HUNGER_DEATH_THRESHOLD)
    world.agents = [target]

    target.die_if_needed(world)
    target.die_if_needed(world)

    assert not target.alive
    assert len(world.death_records) == 1
    assert world.death_records[0].cause_of_death == "starvation"


def test_death_history_entry_is_readable_and_compact():
    world = make_world()
    world.day = 7
    target = Agent("Rowan", 1, 1, agent_id="rowan", role=BUILDER, lifecycle_stage=ELDER, peak_influence_score=24)
    observer = Agent("Ari", 2, 1, agent_id="ari")
    remember(observer, target, score=30, day=7)
    world.agents = [target, observer]

    record = record_death(world, target, "thirst")
    entry = world.history.recent(1)[0]

    assert entry.category == DEATH
    assert entry.title == "Rowan Dies"
    assert entry.description == death_history_description(record)
    assert "Rowan, a respected Elder Builder, died of thirst." in entry.description
    assert "They were remembered by Ari." in entry.description


def test_villager_detail_sections_include_active_remembrance():
    world = make_world()
    world.day = 3
    observer = Agent("Ari", 2, 1, agent_id="ari", remembering="Rowan", remembrance_expires_day=6)

    sections = dict(villager_detail_sections(observer, world))

    assert ("Remembering", "Rowan") in sections["Status"]


def test_death_memory_has_no_gameplay_effects():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan", role=FORAGER)
    observer = Agent("Ari", 2, 1, agent_id="ari", current_goal="Explore", current_action="Idle", hunger=10)
    remember(observer, target, score=30, day=1)
    world.agents = [target, observer]
    before = (
        observer.current_goal,
        observer.current_action,
        observer.hunger,
        observer.thirst,
        observer.fatigue,
        observer.role,
        observer.lifecycle_stage,
        observer.trait,
    )

    record_death(world, target, "thirst")

    assert (
        observer.current_goal,
        observer.current_action,
        observer.hunger,
        observer.thirst,
        observer.fatigue,
        observer.role,
        observer.lifecycle_stage,
        observer.trait,
    ) == before
