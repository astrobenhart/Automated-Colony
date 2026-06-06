from src.world import World
from src.config import COLORS, HEIGHT, TERRAIN_LABELS, WIDTH
from src.tile import Tile


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
    assert first.river_paths == second.river_paths


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


def test_natural_terrain_variety_is_generated():
    world = make_generated_world(seed=22, width=WIDTH, height=HEIGHT)
    kinds = {tile.kind for row in world.tiles for tile in row}

    assert {"hill", "plain", "wetland", "dry"}.issubset(kinds)


def test_all_generated_terrain_kinds_have_colors():
    world = make_generated_world(seed=23, width=WIDTH, height=HEIGHT)
    kinds = {tile.kind for row in world.tiles for tile in row}

    assert kinds.issubset(COLORS.keys())


def test_all_generated_terrain_kinds_have_labels():
    world = make_generated_world(seed=23, width=WIDTH, height=HEIGHT)
    kinds = {tile.kind for row in world.tiles for tile in row}

    assert kinds.issubset(TERRAIN_LABELS.keys())
    assert all(TERRAIN_LABELS[kind] for kind in kinds)


def test_configured_terrain_labels_have_colors():
    assert set(TERRAIN_LABELS).issubset(COLORS.keys())


def test_new_terrain_walkability_rules():
    walkable = ["hill", "plain", "wetland", "dry", "forest", "grass", "shelter"]

    assert all(Tile(kind).walkable for kind in walkable)
    assert not Tile("water").walkable
    assert not Tile("mountain").walkable


def test_forest_tiles_tend_to_have_wood():
    world = make_generated_world(seed=4)
    forests = [tile for row in world.tiles for tile in row if tile.kind == "forest"]
    forests_with_wood = [tile for tile in forests if tile.wood > 0]

    assert forests
    assert len(forests_with_wood) / len(forests) >= 0.9


def test_wetlands_can_have_food():
    world = make_generated_world(seed=24, width=WIDTH, height=HEIGHT)
    wetlands = [tile for row in world.tiles for tile in row if tile.kind == "wetland"]
    wetlands_with_food = [tile for tile in wetlands if tile.food > 0]

    assert wetlands
    assert wetlands_with_food


def test_dry_areas_are_food_sparse():
    world = make_generated_world(seed=25, width=WIDTH, height=HEIGHT)
    dry_tiles = [tile for row in world.tiles for tile in row if tile.kind == "dry"]
    dry_with_food = [tile for tile in dry_tiles if tile.food > 0]

    assert dry_tiles
    assert len(dry_with_food) / len(dry_tiles) <= 0.05


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


def test_mountains_remain_barren():
    world = make_generated_world(seed=26, width=WIDTH, height=HEIGHT)
    mountains = [tile for row in world.tiles for tile in row if tile.kind == "mountain"]

    assert mountains
    assert all(tile.food == 0 and tile.wood == 0 for tile in mountains)


def test_generated_worlds_contain_river_paths():
    world = make_generated_world(seed=12, width=WIDTH, height=HEIGHT)

    assert world.river_paths
    assert any(len(path) >= 8 for path in world.river_paths)


def test_river_path_tiles_are_unwalkable_water():
    world = make_generated_world(seed=13, width=WIDTH, height=HEIGHT)

    river_tiles = {pos for path in world.river_paths for pos in path}

    assert river_tiles
    for x, y in river_tiles:
        tile = world.tile_at(x, y)
        assert tile.kind == "water"
        assert not tile.walkable


def test_at_least_one_river_generally_moves_downhill():
    world = make_generated_world(seed=14, width=WIDTH, height=HEIGHT)

    downhill_paths = []
    for path in world.river_paths:
        start_x, start_y = path[0]
        end_x, end_y = path[-1]
        start_elevation = world.elevation_map[start_y][start_x]
        end_elevation = world.elevation_map[end_y][end_x]
        downhill_paths.append(end_elevation < start_elevation)

    assert any(downhill_paths)
