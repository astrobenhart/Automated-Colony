from src.config import (
    SEASON_FOOD_GROWTH_MODIFIERS,
    SEASON_MOISTURE_MODIFIERS,
    SEASON_WOOD_GROWTH_MODIFIERS,
)
from src.tile import Tile


FOOD_GROWTH_BASE = {
    "wetland": 0.18,
    "forest": 0.045,
    "plain": 0.060,
    "grass": 0.050,
    "hill": 0.025,
    "dry": 0.008,
}

WOOD_GROWTH_BASE = {
    "forest": 0.085,
    "hill": 0.010,
}

FOOD_DIEOFF_BASE = {
    "wetland": 0.004,
    "forest": 0.010,
    "plain": 0.012,
    "grass": 0.014,
    "hill": 0.018,
    "dry": 0.030,
}

WOOD_DIEOFF_BASE = {
    "forest": 0.004,
    "hill": 0.006,
}

FOOD_CAPS = {
    "wetland": 7,
    "forest": 3,
    "plain": 4,
    "grass": 4,
    "hill": 2,
    "dry": 1,
}

WOOD_CAPS = {
    "forest": 8,
    "hill": 2,
}

SEASON_FOOD_DIEOFF_MODIFIERS = {
    "Spring": 0.50,
    "Summer": 1.10,
    "Autumn": 0.80,
    "Winter": 2.20,
}

SEASON_WOOD_DIEOFF_MODIFIERS = {
    "Spring": 0.50,
    "Summer": 0.75,
    "Autumn": 0.90,
    "Winter": 1.35,
}

SUMMER_DRY_FOOD_DIEOFF_MULTIPLIER = 1.8


def max_food(tile: Tile | str) -> int:
    return FOOD_CAPS.get(_kind(tile), 0)


def max_wood(tile: Tile | str) -> int:
    return WOOD_CAPS.get(_kind(tile), 0)


def food_growth_chance(tile: Tile | str, season: str) -> float:
    kind = _kind(tile)
    if max_food(kind) == 0:
        return 0.0

    base = FOOD_GROWTH_BASE.get(kind, 0.0)
    moisture_modifier = SEASON_MOISTURE_MODIFIERS.get(season, 1.0)
    season_modifier = SEASON_FOOD_GROWTH_MODIFIERS.get(season, 1.0)
    return base * moisture_modifier * season_modifier


def wood_growth_chance(tile: Tile | str, season: str) -> float:
    kind = _kind(tile)
    if max_wood(kind) == 0:
        return 0.0

    base = WOOD_GROWTH_BASE.get(kind, 0.0)
    season_modifier = SEASON_WOOD_GROWTH_MODIFIERS.get(season, 1.0)
    return base * season_modifier


def food_dieoff_chance(tile: Tile | str, season: str) -> float:
    kind = _kind(tile)
    if max_food(kind) == 0:
        return 0.0

    base = FOOD_DIEOFF_BASE.get(kind, 0.0)
    season_modifier = SEASON_FOOD_DIEOFF_MODIFIERS.get(season, 1.0)
    if season == "Summer" and kind == "dry":
        season_modifier *= SUMMER_DRY_FOOD_DIEOFF_MULTIPLIER
    return base * season_modifier


def wood_dieoff_chance(tile: Tile | str, season: str) -> float:
    kind = _kind(tile)
    if max_wood(kind) == 0:
        return 0.0

    base = WOOD_DIEOFF_BASE.get(kind, 0.0)
    season_modifier = SEASON_WOOD_DIEOFF_MODIFIERS.get(season, 1.0)
    return base * season_modifier


def apply_resource_ecology(tile: Tile, season: str, rng) -> None:
    food_cap = max_food(tile)
    wood_cap = max_wood(tile)

    if food_cap == 0:
        tile.food = 0
    else:
        tile.food = min(tile.food, food_cap)
        if tile.food > 0 and rng.random() < food_dieoff_chance(tile, season):
            tile.food -= 1
        if tile.food < food_cap and rng.random() < food_growth_chance(tile, season):
            tile.food += 1

    if wood_cap == 0:
        tile.wood = 0
    else:
        tile.wood = min(tile.wood, wood_cap)
        if tile.wood > 0 and rng.random() < wood_dieoff_chance(tile, season):
            tile.wood -= 1
        if tile.wood < wood_cap and rng.random() < wood_growth_chance(tile, season):
            tile.wood += 1


def _kind(tile: Tile | str) -> str:
    if isinstance(tile, str):
        return tile
    return tile.kind
