from src.world import World
from src.config import HEIGHT, WIDTH


def layout_signature(world: World):
    return [
        [(tile.kind, tile.food, tile.wood) for tile in row]
        for row in world.tiles
    ]


def make_generated_world(seed: int, width: int = 50, height: int = 28) -> World:
    world = World(width, height)
    world.generate(seed=seed)
    return world


def test_same_seed_generates_same_world_layout():
    first = make_generated_world(seed=123)
    second = make_generated_world(seed=123)

    assert layout_signature(first) == layout_signature(second)
    assert first.elevation_map == second.elevation_map
    assert first.moisture_map == second.moisture_map
    assert first.temperature_map == second.temperature_map


def test_different_seeds_usually_generate_different_layouts():
    first = make_generated_world(seed=123)
    second = make_generated_world(seed=456)

    assert layout_signature(first) != layout_signature(second)


def test_generated_world_has_expected_dimensions():
    world = make_generated_world(seed=1, width=17, height=9)

    assert len(world.tiles) == 9
    assert all(len(row) == 17 for row in world.tiles)
    assert len(world.elevation_map) == 9
    assert len(world.moisture_map) == 9
    assert len(world.temperature_map) == 9
    assert all(len(row) == 17 for row in world.elevation_map)
    assert all(len(row) == 17 for row in world.moisture_map)
    assert all(len(row) == 17 for row in world.temperature_map)


def test_default_larger_world_dimensions_generate():
    world = make_generated_world(seed=11, width=WIDTH, height=HEIGHT)

    assert len(world.tiles) == HEIGHT
    assert all(len(row) == WIDTH for row in world.tiles)


def test_worldgen_maps_are_normalized():
    world = make_generated_world(seed=2)

    for value_map in (world.elevation_map, world.moisture_map, world.temperature_map):
        for row in value_map:
            for value in row:
                assert 0.0 <= value <= 1.0


def test_core_terrain_types_are_generated():
    world = make_generated_world(seed=3)
    kinds = {tile.kind for row in world.tiles for tile in row}

    assert {"water", "mountain", "forest", "grass"}.issubset(kinds)


def test_forest_tiles_tend_to_have_wood():
    world = make_generated_world(seed=4)
    forests = [tile for row in world.tiles for tile in row if tile.kind == "forest"]
    forests_with_wood = [tile for tile in forests if tile.wood > 0]

    assert forests
    assert len(forests_with_wood) / len(forests) >= 0.9


def test_water_and_mountains_remain_unwalkable():
    world = make_generated_world(seed=5)

    blocked_tiles = [
        tile
        for row in world.tiles
        for tile in row
        if tile.kind in ("water", "mountain")
    ]

    assert blocked_tiles
    assert all(not tile.walkable for tile in blocked_tiles)


def test_water_and_mountains_do_not_have_resources():
    world = make_generated_world(seed=6)

    for row in world.tiles:
        for tile in row:
            if tile.kind in ("water", "mountain"):
                assert tile.food == 0
                assert tile.wood == 0
