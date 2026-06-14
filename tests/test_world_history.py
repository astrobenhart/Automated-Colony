from src.environment_events import (
    create_environment_event,
    maybe_start_environment_event,
    update_environment_events,
)
from src.tile import Tile
from src.world import World
from src.world_history import (
    DEATH,
    ENVIRONMENT,
    HISTORY_CATEGORIES,
    SEASON,
    SETTLEMENT,
    WILDLIFE,
    WorldHistory,
)


class FixedRandom:
    def __init__(self, value: float, randint_value: int = 3):
        self.value = value
        self.randint_value = randint_value

    def random(self):
        return self.value

    def randint(self, _low, _high):
        return self.randint_value


class SequenceRandom:
    def __init__(self, values, randint_value: int = 3):
        self.values = list(values)
        self.randint_value = randint_value

    def random(self):
        return self.values.pop(0)

    def randint(self, _low, _high):
        return self.randint_value


def make_world():
    world = World(2, 2)
    world.tiles = [[Tile("plain"), Tile("water")], [Tile("dry"), Tile("forest")]]
    return world


def test_history_starts_empty_with_future_categories_available():
    history = WorldHistory()

    assert history.count() == 0
    assert {ENVIRONMENT, SEASON, WILDLIFE, SETTLEMENT, DEATH}.issubset(HISTORY_CATEGORIES)


def test_history_records_day_year_season_and_category():
    history = WorldHistory()

    entry = history.record(
        day=12,
        year=1,
        season="Summer",
        category=ENVIRONMENT,
        title="Drought Begins",
        description="The land dries.",
    )

    assert history.count() == 1
    assert entry.day == 12
    assert entry.year == 1
    assert entry.season == "Summer"
    assert entry.category == ENVIRONMENT


def test_history_filters_by_category_and_recent_limit():
    history = WorldHistory()
    history.record(day=1, year=1, season="Spring", category=ENVIRONMENT, title="Rain", description="")
    history.record(day=2, year=1, season="Spring", category=WILDLIFE, title="Herd", description="")
    history.record(day=3, year=1, season="Spring", category=ENVIRONMENT, title="Drought", description="")

    assert [entry.title for entry in history.by_category(ENVIRONMENT)] == ["Rain", "Drought"]
    assert [entry.title for entry in history.recent(2)] == ["Herd", "Drought"]
    assert history.recent(0) == []


def test_world_has_persistent_history():
    world = make_world()

    assert isinstance(world.history, WorldHistory)
    assert world.history.count() == 0


def test_environment_event_start_records_history_separate_from_event_log():
    world = make_world()
    world.day = 7
    world.season_index = 1

    event = maybe_start_environment_event(world, SequenceRandom([0.0, 0.0], randint_value=3))

    assert event is not None
    assert any("begins." in log for log in world.events)
    assert world.history.count() == 1
    entry = world.history.recent(1)[0]
    assert entry.title.endswith("Begins")
    assert entry.day == 7
    assert entry.season == "Summer"
    assert entry.category == ENVIRONMENT
    assert isinstance(world.events[-1], str)


def test_environment_event_end_records_history_without_replacing_event_log():
    world = make_world()
    world.active_environment_events.append(create_environment_event("drought", duration_days=1))

    update_environment_events(world, FixedRandom(1.0))

    assert world.active_environment_events == []
    assert any("The drought ends." in event for event in world.events)
    assert world.history.count() == 1
    assert world.history.recent(1)[0].title == "Drought Ends"
