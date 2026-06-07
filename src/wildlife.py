from __future__ import annotations

import random
from dataclasses import dataclass

from src.config import WILDLIFE_DENSITY, WILDLIFE_MAX_ANIMALS, WILDLIFE_WANDER_CHANCE


@dataclass
class Animal:
    species: str
    x: int
    y: int
    symbol: str
    alive: bool = True


@dataclass(frozen=True)
class SpeciesDefinition:
    species: str
    symbol: str
    suitability: dict[str, int]
    abundance: float


WILDLIFE_SPECIES = {
    "rabbit": SpeciesDefinition(
        species="rabbit",
        symbol="r",
        suitability={"plain": 3, "grass": 3, "hill": 2, "dry": 1},
        abundance=1.30,
    ),
    "deer": SpeciesDefinition(
        species="deer",
        symbol="d",
        suitability={"forest": 3, "plain": 2, "wetland": 2, "grass": 2},
        abundance=0.90,
    ),
    "boar": SpeciesDefinition(
        species="boar",
        symbol="b",
        suitability={"forest": 3, "wetland": 3, "plain": 1},
        abundance=0.55,
    ),
    "waterfowl": SpeciesDefinition(
        species="waterfowl",
        symbol="v",
        suitability={"wetland": 3},
        abundance=1.10,
    ),
}


SEASON_WILDLIFE_MULTIPLIERS = {
    "Spring": 1.15,
    "Summer": 1.00,
    "Autumn": 1.00,
    "Winter": 0.65,
}


def wildlife_population_target(world) -> int:
    density = getattr(getattr(world, "settings", None), "wildlife_density", WILDLIFE_DENSITY)
    base = int(world.width * world.height * density)
    multiplier = SEASON_WILDLIFE_MULTIPLIERS.get(world.season, 1.0)
    return min(WILDLIFE_MAX_ANIMALS, max(0, round(base * multiplier)))


def spawn_wildlife(world, rng: random.Random | None = None, target_count: int | None = None) -> list[Animal]:
    rng = rng or random.Random(world.seed)
    target = wildlife_population_target(world) if target_count is None else target_count
    target = min(target, WILDLIFE_MAX_ANIMALS)

    animals: list[Animal] = []
    occupied_tiles: set[tuple[int, int]] = set()

    for _ in range(target):
        candidates = _spawn_candidates(world, occupied_tiles)
        if not candidates:
            break

        total_weight = sum(weight for _, _, _, weight in candidates)
        choice = rng.uniform(0, total_weight)
        running = 0.0

        for species, x, y, weight in candidates:
            running += weight
            if running >= choice:
                definition = WILDLIFE_SPECIES[species]
                animals.append(Animal(species, x, y, definition.symbol))
                occupied_tiles.add((x, y))
                break

    return animals


def update_wildlife(world, rng=random):
    for animal in list(world.animals):
        if not animal.alive:
            continue
        if rng.random() >= WILDLIFE_WANDER_CHANCE:
            continue

        for nx, ny in _wander_candidates(world, animal, rng):
            if terrain_suitability(world, animal.species, nx, ny) <= 0:
                continue
            if world.agent_at(nx, ny) is not None:
                continue
            if world.animal_at(nx, ny) is not None:
                continue

            animal.x = nx
            animal.y = ny
            break


def terrain_suitability(world, species: str, x: int, y: int) -> int:
    if species not in WILDLIFE_SPECIES:
        return 0
    if not (0 <= x < world.width and 0 <= y < world.height):
        return 0

    tile = world.tile_at(x, y)
    if not tile.walkable or tile.kind == "mountain":
        return 0

    suitability = WILDLIFE_SPECIES[species].suitability.get(tile.kind, 0)
    if species == "waterfowl" and _adjacent_to_water(world, x, y):
        suitability = max(suitability, 3)

    return suitability


def _spawn_candidates(world, occupied_tiles: set[tuple[int, int]]):
    candidates = []

    for y in range(world.height):
        for x in range(world.width):
            if (x, y) in occupied_tiles:
                continue
            if world.agent_at(x, y) is not None:
                continue

            for species, definition in WILDLIFE_SPECIES.items():
                suitability = terrain_suitability(world, species, x, y)
                if suitability > 0:
                    candidates.append((species, x, y, suitability * definition.abundance))

    return candidates


def _wander_candidates(world, animal: Animal, rng) -> list[tuple[int, int]]:
    candidates = [
        (animal.x, animal.y + 1),
        (animal.x + 1, animal.y),
        (animal.x, animal.y - 1),
        (animal.x - 1, animal.y),
    ]
    rng.shuffle(candidates)
    return [
        (x, y)
        for x, y in candidates
        if 0 <= x < world.width and 0 <= y < world.height
    ]


def _adjacent_to_water(world, x: int, y: int) -> bool:
    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nx = x + dx
        ny = y + dy
        if 0 <= nx < world.width and 0 <= ny < world.height:
            if world.tile_at(nx, ny).kind == "water":
                return True
    return False
