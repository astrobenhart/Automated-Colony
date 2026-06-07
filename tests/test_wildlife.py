import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.config import COLORS, SYMBOL_LABELS, WILDLIFE_MAX_ANIMALS
from src.pathfinding import find_path
from src.tile import Tile
from src.wildlife import (
    Animal,
    WILDLIFE_SPECIES,
    spawn_wildlife,
    terrain_suitability,
    update_wildlife,
)
from src.world import World


def make_world(kinds: list[list[str]]) -> World:
    height = len(kinds)
    width = len(kinds[0])
    world = World(width, height, seed=7)
    world.tiles = [[Tile(kind) for kind in row] for row in kinds]
    return world


def animal_signature(world: World):
    return sorted((animal.species, animal.x, animal.y, animal.symbol) for animal in world.animals)


def test_exactly_four_species_are_defined():
    assert set(WILDLIFE_SPECIES) == {"rabbit", "deer", "boar", "waterfowl"}
    assert {definition.symbol for definition in WILDLIFE_SPECIES.values()} == {"r", "d", "b", "v"}


def test_wildlife_spawns_only_on_suitable_terrain():
    world = make_world([
        ["plain", "grass", "hill", "dry", "water"],
        ["forest", "wetland", "plain", "mountain", "grass"],
        ["grass", "plain", "forest", "wetland", "hill"],
    ])

    animals = spawn_wildlife(world, random.Random(3), target_count=20)

    assert animals
    for animal in animals:
        assert terrain_suitability(world, animal.species, animal.x, animal.y) > 0


def test_wildlife_does_not_spawn_on_mountains_or_water():
    world = make_world([
        ["water", "mountain", "plain"],
        ["water", "forest", "wetland"],
        ["mountain", "grass", "hill"],
    ])

    animals = spawn_wildlife(world, random.Random(4), target_count=20)

    for animal in animals:
        assert world.tile_at(animal.x, animal.y).kind not in ("water", "mountain")


def test_wildlife_count_respects_configured_maximum():
    world = make_world([["plain" for _ in range(20)] for _ in range(20)])

    animals = spawn_wildlife(world, random.Random(5), target_count=999)

    assert len(animals) <= WILDLIFE_MAX_ANIMALS


def test_same_seed_produces_deterministic_wildlife_placement():
    first = World(30, 20, seed=123)
    second = World(30, 20, seed=123)

    first.generate()
    second.generate()

    assert animal_signature(first) == animal_signature(second)


def test_animal_wandering_stays_in_bounds_and_suitable_terrain():
    world = make_world([
        ["plain", "plain", "plain"],
        ["plain", "plain", "plain"],
        ["plain", "plain", "plain"],
    ])
    rabbit = Animal("rabbit", 1, 1, "r")
    world.animals.append(rabbit)

    for _ in range(100):
        update_wildlife(world, random.Random(1))
        assert 0 <= rabbit.x < world.width
        assert 0 <= rabbit.y < world.height
        assert terrain_suitability(world, rabbit.species, rabbit.x, rabbit.y) > 0


def test_animals_do_not_block_villager_movement_or_pathfinding():
    world = make_world([["grass", "grass", "grass"]])
    world.animals.append(Animal("rabbit", 1, 0, "r"))

    assert world.can_move_to(1, 0)
    assert find_path(world, (0, 0), (2, 0), avoid_occupied=True) == [(1, 0), (2, 0)]


def test_config_supports_wildlife_symbols_and_color():
    assert COLORS["wildlife"]
    for symbol in ["r", "d", "b", "v"]:
        assert symbol in SYMBOL_LABELS
