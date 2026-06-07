from __future__ import annotations
import random

from src.config import (
    RIVER_MIN_LENGTH,
    RIVER_SOURCE_ELEVATION,
    RIVER_WIDEN_CHANCE,
)
from src.tile import Tile
from src.worldgen_settings import WorldGenSettings, default_worldgen_settings


def generate_world(
    width: int,
    height: int,
    seed: int | None = None,
    settings: WorldGenSettings | None = None,
):
    settings = (settings or default_worldgen_settings()).with_overrides(
        width=width,
        height=height,
        seed=seed,
    )
    rng = random.Random(settings.seed)
    elevation = _normalize_map(_smooth_map(_random_map(width, height, rng), passes=3))
    moisture = _normalize_map(_smooth_map(_random_map(width, height, rng), passes=3))
    temperature = _temperature_map(width, height, rng)
    river_paths = _generate_river_paths(elevation, rng, settings.river_count)
    river_tiles = _river_tile_set(river_paths, elevation, rng)
    _add_river_moisture(moisture, river_tiles)

    tiles: list[list[Tile]] = []

    for y in range(height):
        row: list[Tile] = []

        for x in range(width):
            elev = elevation[y][x]
            moist = moisture[y][x]
            temp = temperature[y][x]
            kind = "water" if (x, y) in river_tiles else _terrain_for(elev, moist, temp, settings)
            tile = Tile(kind)
            _place_resources(tile, moist, temp, rng, settings)
            row.append(tile)

        tiles.append(row)

    return tiles, elevation, moisture, temperature, river_paths


def _random_map(width: int, height: int, rng: random.Random) -> list[list[float]]:
    return [[rng.random() for _ in range(width)] for _ in range(height)]


def _smooth_map(values: list[list[float]], passes: int) -> list[list[float]]:
    smoothed = values

    for _ in range(passes):
        smoothed = _smooth_once(smoothed)

    return smoothed


def _smooth_once(values: list[list[float]]) -> list[list[float]]:
    height = len(values)
    width = len(values[0])
    result: list[list[float]] = []

    for y in range(height):
        row: list[float] = []

        for x in range(width):
            total = 0.0
            count = 0

            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx = x + dx
                    ny = y + dy

                    if 0 <= nx < width and 0 <= ny < height:
                        total += values[ny][nx]
                        count += 1

            row.append(_clamp(total / count))

        result.append(row)

    return result


def _normalize_map(values: list[list[float]]) -> list[list[float]]:
    low = min(value for row in values for value in row)
    high = max(value for row in values for value in row)
    span = high - low

    if span == 0:
        return [[0.5 for _ in row] for row in values]

    return [
        [_clamp((value - low) / span) for value in row]
        for row in values
    ]


def _temperature_map(width: int, height: int, rng: random.Random) -> list[list[float]]:
    noise = _smooth_map(_random_map(width, height, rng), passes=2)
    result: list[list[float]] = []

    for y in range(height):
        latitude = y / max(1, height - 1)
        latitude_temp = 1.0 - abs(latitude - 0.5) * 1.4
        row: list[float] = []

        for x in range(width):
            row.append(_clamp(latitude_temp * 0.75 + noise[y][x] * 0.25))

        result.append(row)

    return result


def _terrain_for(
    elevation: float,
    moisture: float,
    temperature: float,
    settings: WorldGenSettings,
) -> str:
    effective_moisture = _clamp(moisture - settings.climate_harshness * 0.12)

    if elevation < settings.water_level:
        return "water"

    if elevation > settings.mountain_level:
        return "mountain"

    if elevation > 0.64:
        return "hill"

    if elevation < 0.38 and effective_moisture > 0.62:
        return "wetland"

    dry_threshold = 0.28 + settings.climate_harshness * 0.16
    hot_dry_threshold = 0.42 + settings.climate_harshness * 0.12
    if effective_moisture < dry_threshold or (temperature > 0.82 and effective_moisture < hot_dry_threshold):
        return "dry"

    forest_threshold = 0.66 - settings.forest_density * 0.20
    if 0.34 <= elevation <= 0.64 and effective_moisture > forest_threshold and temperature > 0.25:
        return "forest"

    if 0.30 <= elevation <= 0.62 and dry_threshold <= effective_moisture <= 0.66 and temperature > 0.22:
        return "plain"

    return "grass"


def _generate_river_paths(
    elevation: list[list[float]],
    rng: random.Random,
    river_count: int,
) -> list[list[tuple[int, int]]]:
    height = len(elevation)
    width = len(elevation[0])
    candidates = [
        (x, y)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if elevation[y][x] >= RIVER_SOURCE_ELEVATION
    ]
    rng.shuffle(candidates)
    candidates.sort(key=lambda pos: elevation[pos[1]][pos[0]], reverse=True)

    paths: list[list[tuple[int, int]]] = []
    used_sources: list[tuple[int, int]] = []

    for source in candidates:
        if len(paths) >= river_count:
            break
        if any(_distance(source, existing) < max(6, RIVER_MIN_LENGTH) for existing in used_sources):
            continue

        path = _trace_river(elevation, source, rng)
        if len(path) >= RIVER_MIN_LENGTH and _drops_downhill(elevation, path):
            paths.append(path)
            used_sources.append(source)

    return paths


def _trace_river(
    elevation: list[list[float]],
    source: tuple[int, int],
    rng: random.Random,
) -> list[tuple[int, int]]:
    height = len(elevation)
    width = len(elevation[0])
    max_length = width + height
    current = source
    path = [current]
    visited = {current}

    for _ in range(max_length):
        x, y = current
        if len(path) >= RIVER_MIN_LENGTH:
            if _is_edge(x, y, width, height) or elevation[y][x] < 0.30:
                break

        candidates = [
            (nx, ny)
            for nx, ny in _neighbor_positions(x, y, width, height)
            if (nx, ny) not in visited
        ]
        if not candidates:
            break

        current_elevation = elevation[y][x]
        downhill = [
            pos
            for pos in candidates
            if elevation[pos[1]][pos[0]] <= current_elevation + 0.01
        ]
        if not downhill:
            break

        lowest = min(elevation[pos[1]][pos[0]] for pos in downhill)
        best = [pos for pos in downhill if elevation[pos[1]][pos[0]] <= lowest + 0.02]
        current = rng.choice(best)
        path.append(current)
        visited.add(current)

    return path


def _river_tile_set(
    paths: list[list[tuple[int, int]]],
    elevation: list[list[float]],
    rng: random.Random,
) -> set[tuple[int, int]]:
    height = len(elevation)
    width = len(elevation[0])
    river_tiles: set[tuple[int, int]] = set()

    for path in paths:
        for x, y in path:
            river_tiles.add((x, y))

            if rng.random() >= RIVER_WIDEN_CHANCE:
                continue

            candidates = _neighbor_positions(x, y, width, height)
            if candidates:
                river_tiles.add(min(candidates, key=lambda pos: elevation[pos[1]][pos[0]]))

    return river_tiles


def _add_river_moisture(moisture: list[list[float]], river_tiles: set[tuple[int, int]]):
    height = len(moisture)
    width = len(moisture[0])

    for x, y in river_tiles:
        for ny in range(max(0, y - 1), min(height, y + 2)):
            for nx in range(max(0, x - 1), min(width, x + 2)):
                distance = abs(nx - x) + abs(ny - y)
                boost = 0.20 if distance == 0 else 0.10
                moisture[ny][nx] = _clamp(moisture[ny][nx] + boost)


def _neighbor_positions(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []

    for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nx = x + dx
        ny = y + dy
        if 0 <= nx < width and 0 <= ny < height:
            candidates.append((nx, ny))

    return candidates


def _drops_downhill(elevation: list[list[float]], path: list[tuple[int, int]]) -> bool:
    start_x, start_y = path[0]
    end_x, end_y = path[-1]
    return elevation[end_y][end_x] < elevation[start_y][start_x]


def _is_edge(x: int, y: int, width: int, height: int) -> bool:
    return x == 0 or y == 0 or x == width - 1 or y == height - 1


def _distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def _place_resources(
    tile: Tile,
    moisture: float,
    temperature: float,
    rng: random.Random,
    settings: WorldGenSettings,
):
    abundance = settings.resource_abundance
    harshness = settings.climate_harshness

    if tile.kind == "forest":
        tile.wood = _scaled_amount(rng.randint(2, 5), abundance)

        if moisture > 0.55 and 0.25 < temperature < 0.9 and rng.random() < 0.28 * abundance:
            tile.food = _scaled_amount(rng.randint(1, 2), abundance)

    elif tile.kind == "wetland":
        if rng.random() < 0.24 * abundance:
            tile.food = _scaled_amount(rng.randint(1, 3), abundance)

    elif tile.kind in ("plain", "grass"):
        fertile = moisture > 0.45 and 0.25 < temperature < 0.85
        food_chance = 0.10 if tile.kind == "plain" and fertile else 0.06 if fertile else 0.02

        if rng.random() < food_chance * abundance * (1.0 - harshness * 0.25):
            tile.food = _scaled_amount(rng.randint(1, 3), abundance)

    elif tile.kind == "hill":
        if moisture > 0.48 and temperature > 0.25 and rng.random() < 0.05 * abundance:
            tile.food = 1

        if moisture > 0.58 and rng.random() < 0.12 * abundance:
            tile.wood = _scaled_amount(rng.randint(1, 2), abundance)

    elif tile.kind == "dry":
        if rng.random() < 0.01 * abundance * (1.0 - harshness * 0.35):
            tile.food = 1


def _scaled_amount(amount: int, abundance: float) -> int:
    if amount <= 0 or abundance <= 0:
        return 0
    return max(1, round(amount * abundance))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
