from dataclasses import dataclass

from src.config import (
    ENV_EVENT_CHANCE_PER_DAY,
    ENV_EVENT_MAX_DURATION_DAYS,
    ENV_EVENT_MIN_DURATION_DAYS,
    MAX_ACTIVE_ENV_EVENTS,
)


@dataclass
class EnvironmentalEvent:
    name: str
    effect_type: str
    duration_days: int
    remaining_days: int
    description: str


EVENT_DEFINITIONS = {
    "drought": {
        "name": "Drought",
        "description": "The land dries under a stubborn hot sky.",
        "start": "A drought begins.",
        "end": "The drought ends.",
        "season_weights": {
            "Spring": 0.7,
            "Summer": 3.0,
            "Autumn": 0.8,
            "Winter": 0.2,
        },
    },
    "heavy_rain": {
        "name": "Heavy Rain",
        "description": "Heavy rain soaks the soil and fills low ground.",
        "start": "Heavy rain begins.",
        "end": "Heavy rain ends.",
        "season_weights": {
            "Spring": 2.4,
            "Summer": 0.8,
            "Autumn": 2.0,
            "Winter": 0.6,
        },
    },
}


DROUGHT_DRY_TERRAINS = {"dry", "plain", "grass", "wetland"}
RAIN_FERTILE_TERRAINS = {"wetland", "plain", "grass", "forest", "dry"}


def create_environment_event(effect_type: str, duration_days: int) -> EnvironmentalEvent:
    definition = EVENT_DEFINITIONS[effect_type]
    return EnvironmentalEvent(
        name=definition["name"],
        effect_type=effect_type,
        duration_days=duration_days,
        remaining_days=duration_days,
        description=definition["description"],
    )


def update_environment_events(world, rng) -> None:
    ended_events = []
    for event in world.active_environment_events:
        event.remaining_days -= 1
        if event.remaining_days <= 0:
            ended_events.append(event)

    for event in ended_events:
        world.active_environment_events.remove(event)
        world.log(EVENT_DEFINITIONS[event.effect_type]["end"])

    maybe_start_environment_event(world, rng)


def maybe_start_environment_event(world, rng) -> EnvironmentalEvent | None:
    if len(world.active_environment_events) >= MAX_ACTIVE_ENV_EVENTS:
        return None

    active_types = {event.effect_type for event in world.active_environment_events}
    candidates = [
        effect_type
        for effect_type in EVENT_DEFINITIONS
        if effect_type not in active_types
    ]
    if not candidates:
        return None

    if rng.random() >= ENV_EVENT_CHANCE_PER_DAY:
        return None

    effect_type = choose_event_type(world.season, candidates, rng)
    duration = rng.randint(ENV_EVENT_MIN_DURATION_DAYS, ENV_EVENT_MAX_DURATION_DAYS)
    event = create_environment_event(effect_type, duration)
    world.active_environment_events.append(event)
    world.log(EVENT_DEFINITIONS[effect_type]["start"])
    return event


def choose_event_type(season: str, candidates: list[str], rng) -> str:
    weighted: list[tuple[str, float]] = []
    total = 0.0
    for effect_type in candidates:
        weight = EVENT_DEFINITIONS[effect_type]["season_weights"].get(season, 1.0)
        weighted.append((effect_type, weight))
        total += weight

    roll = rng.random() * total
    running = 0.0
    for effect_type, weight in weighted:
        running += weight
        if roll <= running:
            return effect_type

    return weighted[-1][0]


def food_growth_event_multiplier(tile_kind: str, events) -> float:
    multiplier = 1.0
    for event in events:
        if event.effect_type == "drought" and tile_kind in DROUGHT_DRY_TERRAINS:
            multiplier *= 0.72
        elif event.effect_type == "heavy_rain" and tile_kind in RAIN_FERTILE_TERRAINS:
            multiplier *= 1.35
    return multiplier


def food_dieoff_event_multiplier(tile_kind: str, events) -> float:
    multiplier = 1.0
    for event in events:
        if event.effect_type == "drought" and tile_kind in {"dry", "plain", "grass"}:
            multiplier *= 1.45
        elif event.effect_type == "drought" and tile_kind == "wetland":
            multiplier *= 1.20
        elif event.effect_type == "heavy_rain" and tile_kind in RAIN_FERTILE_TERRAINS:
            multiplier *= 0.70
    return multiplier


def wood_growth_event_multiplier(tile_kind: str, events) -> float:
    multiplier = 1.0
    for event in events:
        if event.effect_type == "drought" and tile_kind == "forest":
            multiplier *= 0.85
        elif event.effect_type == "heavy_rain" and tile_kind == "forest":
            multiplier *= 1.12
    return multiplier


def environmental_tile_color(color: tuple[int, int, int], tile_kind: str, events) -> tuple[int, int, int]:
    result = color
    for event in events:
        if event.effect_type == "drought" and tile_kind in {"dry", "plain", "grass", "wetland", "forest"}:
            result = _blend_color(result, (188, 148, 78), 0.22)
        elif event.effect_type == "heavy_rain" and tile_kind in {"wetland", "plain", "grass", "forest", "water", "dry"}:
            result = _blend_color(result, (54, 126, 112), 0.20)
    return result


def active_event_names(events) -> str:
    if not events:
        return "None"
    return ", ".join(f"{event.name} {event.remaining_days}d" for event in events)


def _blend_color(
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    progress: float,
) -> tuple[int, int, int]:
    return tuple(
        round(start + (end - start) * progress)
        for start, end in zip(color_a, color_b)
    )
