from src.config import MAX_ACTIVE_ENV_EVENTS
from src.environment_events import (
    EnvironmentalEvent,
    active_event_names,
    create_environment_event,
    environmental_tile_color,
    maybe_start_environment_event,
    update_environment_events,
)
from src.resource_ecology import food_dieoff_chance, food_growth_chance
from src.tile import Tile
from src.world import World, create_world


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


def test_environmental_events_can_be_created():
    event = create_environment_event("drought", duration_days=4)

    assert event.name == "Drought"
    assert event.effect_type == "drought"
    assert event.duration_days == 4
    assert event.remaining_days == 4


def test_events_tick_down_and_expire_with_end_log():
    world = make_world()
    world.active_environment_events.append(create_environment_event("drought", duration_days=1))

    update_environment_events(world, FixedRandom(1.0))

    assert world.active_environment_events == []
    assert any("The drought ends." in event for event in world.events)


def test_event_start_is_logged_and_stored_on_world():
    world = make_world()
    world.season_index = 1

    event = maybe_start_environment_event(world, SequenceRandom([0.0, 0.0], randint_value=3))

    assert event is not None
    assert event in world.active_environment_events
    assert any("begins." in log for log in world.events)


def test_drought_reduces_food_growth_and_increases_dieoff():
    drought = [create_environment_event("drought", duration_days=3)]

    assert food_growth_chance("plain", "Summer", drought) < food_growth_chance("plain", "Summer")
    assert food_dieoff_chance("plain", "Summer", drought) > food_dieoff_chance("plain", "Summer")


def test_drought_does_not_remove_permanent_water_or_rivers():
    world = create_world(seed=31, agent_count=0)
    starting_water = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == "water"
    }
    world.active_environment_events.append(create_environment_event("drought", duration_days=3))

    for _ in range(3):
        world.advance_day()

    ending_water = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == "water"
    }

    assert starting_water == ending_water


def test_heavy_rain_increases_food_growth_and_reduces_dieoff():
    rain = [create_environment_event("heavy_rain", duration_days=3)]

    assert food_growth_chance("wetland", "Spring", rain) > food_growth_chance("wetland", "Spring")
    assert food_dieoff_chance("dry", "Spring", rain) < food_dieoff_chance("dry", "Spring")


def test_max_active_event_limit_is_respected():
    world = make_world()
    for _ in range(MAX_ACTIVE_ENV_EVENTS):
        world.active_environment_events.append(create_environment_event("drought", duration_days=3))

    event = maybe_start_environment_event(world, FixedRandom(0.0))

    assert event is None
    assert len(world.active_environment_events) == MAX_ACTIVE_ENV_EVENTS


def test_active_event_names_are_compact():
    events = [create_environment_event("heavy_rain", duration_days=2)]

    assert active_event_names(events) == "Heavy Rain 2d"


def test_environment_event_tint_changes_visible_tile_color():
    event = create_environment_event("drought", duration_days=3)
    base = (100, 150, 80)

    tinted = environmental_tile_color(base, "plain", [event])

    assert tinted != base
