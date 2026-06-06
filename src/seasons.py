from src.config import (
    DAYS_PER_SEASON,
    SEASONS,
    SEASON_FOOD_GROWTH_MODIFIERS,
    SEASON_MOISTURE_MODIFIERS,
    SEASON_WOOD_GROWTH_MODIFIERS,
)


BASE_FOOD_GROWTH = {
    "wetland": 0.16,
    "forest": 0.045,
    "plain": 0.055,
    "grass": 0.045,
    "hill": 0.025,
    "dry": 0.006,
}

BASE_WOOD_GROWTH = {
    "forest": 0.080,
    "hill": 0.010,
}


def season_for_index(index: int) -> str:
    return SEASONS[index % len(SEASONS)]


def next_season_index(index: int) -> int:
    return (index + 1) % len(SEASONS)


def day_of_season(day: int) -> int:
    return ((day - 1) % DAYS_PER_SEASON) + 1


def should_advance_season(day: int) -> bool:
    return day > 1 and day_of_season(day) == 1


def food_growth_chance(tile_kind: str, season: str) -> float:
    base = BASE_FOOD_GROWTH.get(tile_kind, 0.0)
    if base == 0.0:
        return 0.0

    moisture_modifier = SEASON_MOISTURE_MODIFIERS.get(season, 1.0)
    season_modifier = SEASON_FOOD_GROWTH_MODIFIERS.get(season, 1.0)
    return base * moisture_modifier * season_modifier


def wood_growth_chance(tile_kind: str, season: str) -> float:
    base = BASE_WOOD_GROWTH.get(tile_kind, 0.0)
    if base == 0.0:
        return 0.0

    season_modifier = SEASON_WOOD_GROWTH_MODIFIERS.get(season, 1.0)
    return base * season_modifier
