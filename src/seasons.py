from src.config import (
    COLORS,
    DAYS_PER_SEASON,
    SEASONS,
    SEASON_FOOD_GROWTH_MODIFIERS,
    SEASON_MOISTURE_MODIFIERS,
    SEASON_WOOD_GROWTH_MODIFIERS,
    SEASONAL_TERRAIN_COLORS,
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


def transition_progress(
    season_day: int,
    ticks_into_day: int,
    ticks_per_day: int,
) -> float:
    if season_day != DAYS_PER_SEASON:
        return 0.0

    if ticks_per_day <= 1:
        return 1.0

    return _clamp(ticks_into_day / (ticks_per_day - 1))


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


def lerp_color(
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    progress: float,
) -> tuple[int, int, int]:
    progress = _clamp(progress)
    return tuple(
        round(start + (end - start) * progress)
        for start, end in zip(color_a, color_b)
    )


def seasonal_tile_color(
    tile_kind: str,
    season: str,
    next_season: str | None = None,
    progress: float = 0.0,
) -> tuple[int, int, int]:
    season_colors = SEASONAL_TERRAIN_COLORS.get(season, {})
    current_color = season_colors.get(tile_kind, COLORS[tile_kind])

    if next_season is None or progress <= 0.0:
        return current_color

    next_colors = SEASONAL_TERRAIN_COLORS.get(next_season, {})
    next_color = next_colors.get(tile_kind, COLORS[tile_kind])
    return lerp_color(current_color, next_color, progress)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
