from __future__ import annotations
import random

from src.tile import Tile


def generate_world(width: int, height: int, seed: int | None = None):
    rng = random.Random(seed)
    elevation = _normalize_map(_smooth_map(_random_map(width, height, rng), passes=3))
    moisture = _normalize_map(_smooth_map(_random_map(width, height, rng), passes=3))
    temperature = _temperature_map(width, height, rng)

    tiles: list[list[Tile]] = []

    for y in range(height):
        row: list[Tile] = []

        for x in range(width):
            elev = elevation[y][x]
            moist = moisture[y][x]
            temp = temperature[y][x]
            kind = _terrain_for(elev, moist, temp)
            tile = Tile(kind)
            _place_resources(tile, moist, temp, rng)
            row.append(tile)

        tiles.append(row)

    return tiles, elevation, moisture, temperature


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


def _terrain_for(elevation: float, moisture: float, temperature: float) -> str:
    if elevation < 0.28:
        return "water"

    if elevation > 0.74:
        return "mountain"

    if 0.30 <= elevation <= 0.72 and moisture > 0.55 and temperature > 0.25:
        return "forest"

    return "grass"


def _place_resources(tile: Tile, moisture: float, temperature: float, rng: random.Random):
    if tile.kind == "forest":
        tile.wood = rng.randint(2, 5)

        if moisture > 0.55 and 0.25 < temperature < 0.9 and rng.random() < 0.28:
            tile.food = rng.randint(1, 2)

    elif tile.kind == "grass":
        fertile = moisture > 0.45 and 0.25 < temperature < 0.85
        food_chance = 0.12 if fertile else 0.03

        if rng.random() < food_chance:
            tile.food = rng.randint(1, 3)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
