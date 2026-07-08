from __future__ import annotations
import random
from dataclasses import dataclass

from src.config import (
    RIVER_MIN_LENGTH,
    RIVER_WIDEN_CHANCE,
)
from src.tile import Tile
from src.worldgen_settings import WorldGenSettings, default_worldgen_settings


@dataclass(frozen=True)
class LakeFeature:
    center: tuple[int, int]
    tiles: frozenset[tuple[int, int]]


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
    lakes = _generate_lakes(width, height, elevation, rng, settings)
    river_paths = _generate_river_paths(width, height, elevation, rng, settings, lakes)
    river_tiles = _river_tile_set(river_paths, elevation, rng)
    lake_tiles = {pos for lake in lakes for pos in lake.tiles}
    water_tiles = river_tiles | lake_tiles
    _add_river_moisture(moisture, water_tiles)

    tiles: list[list[Tile]] = []

    for y in range(height):
        row: list[Tile] = []

        for x in range(width):
            elev = elevation[y][x]
            moist = moisture[y][x]
            temp = temperature[y][x]
            kind = "water" if (x, y) in water_tiles else _terrain_for(elev, moist, temp, settings)
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
    width: int,
    height: int,
    elevation: list[list[float]],
    rng: random.Random,
    settings: WorldGenSettings,
    lakes: list[LakeFeature],
) -> list[list[tuple[int, int]]]:
    if width <= 2 or height <= 2 or settings.river_count <= 0:
        return []

    paths: list[list[tuple[int, int]]] = []
    high_edge = _edge_point_by_elevation(width, height, elevation, highest=True, rng=rng)
    low_edge = _edge_point_by_elevation(
        width,
        height,
        elevation,
        highest=False,
        rng=rng,
        exclude_edge=_edge_name(high_edge, width, height),
    )

    if lakes:
        primary = lakes[0]
        inlet = _nearest_lake_edge(primary, high_edge)
        path = _trace_feature_river(width, height, high_edge, inlet, rng)
        if len(path) >= RIVER_MIN_LENGTH:
            paths.append(path)

        if len(paths) < settings.river_count:
            outlet = _nearest_lake_edge(primary, low_edge)
            path = _trace_feature_river(width, height, outlet, low_edge, rng)
            if len(path) >= RIVER_MIN_LENGTH:
                paths.append(path)

        if len(lakes) > 1 and len(paths) < settings.river_count:
            first = lakes[0]
            second = lakes[1]
            path = _trace_feature_river(
                width,
                height,
                _nearest_lake_edge(first, second.center),
                _nearest_lake_edge(second, first.center),
                rng,
            )
            if len(path) >= RIVER_MIN_LENGTH:
                paths.append(path)
    else:
        path = _trace_feature_river(width, height, high_edge, low_edge, rng)
        if len(path) >= RIVER_MIN_LENGTH:
            paths.append(path)

    candidate_edges = ["north", "south", "west", "east"]
    rng.shuffle(candidate_edges)
    while len(paths) < settings.river_count and candidate_edges:
        start_edge = candidate_edges.pop()
        end_edge = _opposite_edge(start_edge)
        path = _trace_feature_river(
            width,
            height,
            _random_edge_point(width, height, start_edge, rng),
            _random_edge_point(width, height, end_edge, rng),
            rng,
        )
        if len(path) >= RIVER_MIN_LENGTH:
            paths.append(path)

    return paths


def _generate_lakes(
    width: int,
    height: int,
    elevation: list[list[float]],
    rng: random.Random,
    settings: WorldGenSettings,
) -> list[LakeFeature]:
    if min(width, height) < 14:
        return []

    count = _target_lake_count(width, height, settings, rng)
    if count <= 0:
        return []

    margin = max(4, min(width, height) // 8)
    candidates = [
        (x, y)
        for y in range(margin, height - margin)
        for x in range(margin, width - margin)
    ]
    rng.shuffle(candidates)
    candidates.sort(key=lambda pos: (elevation[pos[1]][pos[0]], rng.random()))

    lakes: list[LakeFeature] = []
    minimum_spacing = max(8, min(width, height) // 3)
    for center in candidates:
        if len(lakes) >= count:
            break
        if any(_distance(center, existing.center) < minimum_spacing for existing in lakes):
            continue
        lake = _make_lake_feature(width, height, center, elevation, rng, settings)
        if len(lake.tiles) >= _minimum_lake_size(width, height):
            lakes.append(lake)

    return lakes


def _target_lake_count(width: int, height: int, settings: WorldGenSettings, rng: random.Random) -> int:
    area = width * height
    if area < 420:
        return 0 if settings.water_level < 0.30 and rng.random() < 0.35 else 1
    if settings.water_level >= 0.32:
        return 2
    if settings.water_level <= 0.23:
        return 0 if rng.random() < 0.55 else 1
    return 1 if rng.random() < 0.72 else 2


def _make_lake_feature(
    width: int,
    height: int,
    center: tuple[int, int],
    elevation: list[list[float]],
    rng: random.Random,
    settings: WorldGenSettings,
) -> LakeFeature:
    cx, cy = center
    size_factor = 0.85 + settings.water_level * 1.6
    rx = max(3, int(rng.randint(3, 6) * size_factor * width / 50))
    ry = max(2, int(rng.randint(2, 5) * size_factor * height / 28))
    tiles: set[tuple[int, int]] = set()

    for y in range(max(1, cy - ry - 2), min(height - 1, cy + ry + 3)):
        for x in range(max(1, cx - rx - 2), min(width - 1, cx + rx + 3)):
            nx = (x - cx) / max(1, rx)
            ny = (y - cy) / max(1, ry)
            shoreline_noise = rng.uniform(-0.22, 0.20)
            elevation_bias = max(0.0, elevation[y][x] - elevation[cy][cx]) * 0.45
            if nx * nx + ny * ny + elevation_bias <= 1.0 + shoreline_noise:
                tiles.add((x, y))

    if len(tiles) < _minimum_lake_size(width, height):
        fallback_radius = max(2, min(rx, ry))
        for y in range(max(1, cy - fallback_radius), min(height - 1, cy + fallback_radius + 1)):
            for x in range(max(1, cx - fallback_radius), min(width - 1, cx + fallback_radius + 1)):
                if _distance((x, y), center) <= fallback_radius:
                    tiles.add((x, y))

    return LakeFeature(center=center, tiles=frozenset(tiles))


def _minimum_lake_size(width: int, height: int) -> int:
    return max(8, min(24, (width * height) // 90))


def _trace_feature_river(
    width: int,
    height: int,
    start: tuple[int, int],
    target: tuple[int, int],
    rng: random.Random,
) -> list[tuple[int, int]]:
    current = start
    path = [current]

    for _ in range(width * height):
        if current == target:
            break
        x, y = current
        candidates = _neighbor_positions(x, y, width, height)
        candidates.sort(key=lambda pos: (_distance(pos, target), rng.random()))
        current = candidates[0]
        path.append(current)

    return _dedupe_consecutive(path)


def _edge_point_by_elevation(
    width: int,
    height: int,
    elevation: list[list[float]],
    *,
    highest: bool,
    rng: random.Random,
    exclude_edge: str | None = None,
) -> tuple[int, int]:
    candidates = []
    for edge in ("north", "south", "west", "east"):
        if edge == exclude_edge:
            continue
        for pos in _edge_positions(width, height, edge):
            x, y = pos
            candidates.append((elevation[y][x], rng.random(), pos))

    if not candidates:
        return (0, 0)
    candidates.sort(reverse=highest)
    return candidates[0][2]


def _edge_positions(width: int, height: int, edge: str) -> list[tuple[int, int]]:
    if edge == "north":
        return [(x, 0) for x in range(width)]
    if edge == "south":
        return [(x, height - 1) for x in range(width)]
    if edge == "west":
        return [(0, y) for y in range(height)]
    return [(width - 1, y) for y in range(height)]


def _edge_name(pos: tuple[int, int], width: int, height: int) -> str:
    x, y = pos
    if y == 0:
        return "north"
    if y == height - 1:
        return "south"
    if x == 0:
        return "west"
    return "east"


def _opposite_edge(edge: str) -> str:
    return {
        "north": "south",
        "south": "north",
        "west": "east",
        "east": "west",
    }[edge]


def _random_edge_point(width: int, height: int, edge: str, rng: random.Random) -> tuple[int, int]:
    return rng.choice(_edge_positions(width, height, edge))


def _nearest_lake_edge(lake: LakeFeature, target: tuple[int, int]) -> tuple[int, int]:
    return min(lake.tiles, key=lambda pos: (_distance(pos, target), pos[1], pos[0]))


def _dedupe_consecutive(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for pos in path:
        if result and result[-1] == pos:
            continue
        result.append(pos)
    return result


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
