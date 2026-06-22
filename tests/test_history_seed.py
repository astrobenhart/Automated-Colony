from src.history_seed import seed_starting_chronicle
from src.overlays.history import chronicle_date, history_event_lines
from src.world import create_world
from src.world_history import ENVIRONMENT, HOUSEHOLD, LOCAL_STORY, MYSTERY, POPULATION, SETTLEMENT, WORKPLACE


def test_starting_chronicle_seeds_multiple_history_categories():
    world = create_world(seed=401, agent_count=45)
    categories = {entry.category for entry in world.history.entries}

    assert world.history.count() >= 12
    assert {SETTLEMENT, HOUSEHOLD, WORKPLACE, POPULATION, ENVIRONMENT, LOCAL_STORY, MYSTERY} <= categories


def test_starting_chronicle_is_grounded_in_generated_settlement_state():
    world = create_world(seed=402, agent_count=45)
    text = "\n".join(entry.description for entry in world.history.entries)

    assert world.settlement.name in text
    assert any(household.household_name in text for household in world.settlement.households)
    assert any("storage" in entry.description.lower() for entry in world.history.entries)
    assert any(entry.title.startswith("Population Reached") for entry in world.history.entries)


def test_starting_chronicle_records_personal_local_stories():
    world = create_world(seed=403, agent_count=45)
    stories = world.history.by_category(LOCAL_STORY)

    assert stories
    assert any(agent.name in story.description for agent in world.agents for story in stories)
    assert all("remembered" in story.description for story in stories)


def test_starting_chronicle_includes_unresolved_mystery_without_mechanics():
    world = create_world(seed=404, agent_count=45)
    mysteries = world.history.by_category(MYSTERY)

    assert len(mysteries) == 1
    description = mysteries[0].description.lower()
    assert "monster" not in description
    assert "combat" not in description
    assert "explained" not in description


def test_seeded_entries_precede_new_simulation_history_in_storage_and_overlay():
    world = create_world(seed=405, agent_count=45)
    seeded_count = world.history.count()
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=SETTLEMENT,
        title="New Event",
        description="A new event happened after observation began.",
    )

    assert world.history.entries[seeded_count].title == "New Event"
    assert history_event_lines(world)[0].text.endswith("A new event happened after observation began.")


def test_starting_chronicle_seeding_is_idempotent():
    world = create_world(seed=406, agent_count=45)
    count = world.history.count()

    seed_starting_chronicle(world)

    assert world.history.count() == count


def test_chronicle_date_supports_prehistory_year_zero():
    assert chronicle_date("Spring", 0, day=1) == "Spring, Year 0"
