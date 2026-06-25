from __future__ import annotations

import hashlib

from src.config import FOREST_SEASON_TRANSITION_DAYS, SEASONS


Color = tuple[int, int, int]


FOREST_SUBCELL_COUNT = 2

FOREST_SEASON_PALETTES: dict[str, tuple[Color, ...]] = {
    "Spring": (
        (34, 104, 44),
        (42, 116, 48),
        (50, 128, 54),
        (62, 140, 60),
        (86, 158, 72),
    ),
    "Summer": (
        (18, 72, 32),
        (26, 92, 38),
        (36, 118, 44),
        (54, 146, 50),
        (72, 164, 58),
        (104, 70, 42),
    ),
    "Autumn": (
        (48, 104, 42),
        (94, 130, 42),
        (156, 136, 42),
        (186, 104, 36),
        (152, 62, 38),
        (112, 78, 34),
    ),
    "Winter": (
        (58, 44, 34),
        (76, 56, 40),
        (92, 74, 54),
        (102, 96, 78),
        (38, 82, 54),
    ),
}

FOREST_SEASON_WEIGHTS: dict[str, tuple[int, ...]] = {
    "Spring": (30, 34, 24, 10, 2),
    "Summer": (32, 34, 20, 9, 3, 2),
    "Autumn": (22, 22, 24, 18, 10, 4),
    "Winter": (30, 30, 24, 12, 4),
}


def forest_transition_cache_key(world) -> tuple[str, int]:
    season = getattr(world, "season", "Spring")
    day_of_season = getattr(world, "day_of_season", 1)
    return (season, min(day_of_season, FOREST_SEASON_TRANSITION_DAYS + 1))


def forest_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    season: str,
    day_of_season: int,
) -> tuple[Color, Color, Color, Color]:
    visual_season = forest_visual_season(seed, tile_x, tile_y, season, day_of_season)
    return _season_subcell_colors(seed, tile_x, tile_y, visual_season)


def forest_visual_season(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    season: str,
    day_of_season: int,
) -> str:
    if day_of_season <= 0:
        return season
    transition_day = forest_transition_day(seed, tile_x, tile_y, season)
    if day_of_season < transition_day:
        return previous_season(season)
    return season


def forest_transition_day(seed: int | None, tile_x: int, tile_y: int, season: str) -> int:
    duration = max(1, FOREST_SEASON_TRANSITION_DAYS)
    return (_stable_int(seed, tile_x, tile_y, season, "season-transition") % duration) + 1


def previous_season(season: str) -> str:
    if season not in SEASONS:
        return season
    index = SEASONS.index(season)
    return SEASONS[(index - 1) % len(SEASONS)]


def _season_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    season: str,
) -> tuple[Color, Color, Color, Color]:
    palette = FOREST_SEASON_PALETTES.get(season, FOREST_SEASON_PALETTES["Spring"])
    weights = FOREST_SEASON_WEIGHTS.get(season, FOREST_SEASON_WEIGHTS["Spring"])
    colors = []
    for subcell in range(4):
        roll = _stable_int(seed, tile_x, tile_y, season, subcell)
        colors.append(_weighted_color(palette, weights, roll))
    return tuple(colors)  # type: ignore[return-value]


def _weighted_color(palette: tuple[Color, ...], weights: tuple[int, ...], roll: int) -> Color:
    total = max(1, sum(weights))
    marker = roll % total
    running = 0
    for color, weight in zip(palette, weights):
        running += weight
        if marker < running:
            return color
    return palette[-1]


def _stable_int(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")
