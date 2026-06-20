from src.config import (
    PATH_TRAFFIC_DAILY_DECAY,
    PATH_TRAFFIC_DIRT_THRESHOLD,
    PATH_TRAFFIC_ESTABLISHED_THRESHOLD,
    PATH_TRAFFIC_PRESEEDED,
    PATH_TRAFFIC_TRAMPLED_THRESHOLD,
    PATH_TRAFFIC_WORN_THRESHOLD,
)
from src.settlement import Home, Settlement, Stockpile
from src.tile import Tile
from src.village_paths import (
    DIRT_PATH,
    PATH,
    TRAMPLED_GRASS,
    WORN_GRASS,
    apply_path_wear,
    decay_foot_traffic,
    path_border_edges,
    record_foot_traffic,
    seed_village_paths,
)
from src.workshop import Workshop
from src.world import World, create_world


def make_world(width: int, height: int, kind: str = "grass") -> World:
    world = World(width, height)
    world.tiles = [[Tile(kind) for _ in range(width)] for _ in range(height)]
    return world


def test_starting_village_has_preseeded_paths_near_homes():
    world = create_world(seed=71, agent_count=0)
    path_tiles = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == PATH
    }

    assert path_tiles
    assert all(world.tile_at(x, y).foot_traffic >= PATH_TRAFFIC_PRESEEDED for x, y in path_tiles)
    for home in world.settlement.homes:
        assert any(max(abs(px - home.x), abs(py - home.y)) <= 1 for px, py in path_tiles)
        assert world.tile_at(home.x, home.y).kind == "home"


def test_village_paths_connect_service_sites_without_overwriting_them():
    world = create_world(seed=72, agent_count=0)
    path_tiles = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == PATH
    }

    for stockpile in world.settlement.stockpiles:
        assert (stockpile.x, stockpile.y) not in path_tiles
        assert any(max(abs(px - stockpile.x), abs(py - stockpile.y)) <= 1 for px, py in path_tiles)

    for workshop in world.settlement.workshops:
        assert (workshop.x, workshop.y) not in path_tiles
        assert any(max(abs(px - workshop.x), abs(py - workshop.y)) <= 1 for px, py in path_tiles)


def test_seeded_paths_connect_water_access_when_water_is_nearby():
    world = make_world(12, 12)
    world.tiles[6][9].kind = "water"
    settlement = Settlement("Testhold", 4, 6, 1, "Spring", radius=5, resource_radius=8)
    settlement.homes = [Home(2, 6, "home-0")]
    settlement.stockpiles = [Stockpile(5, 6, "food")]
    settlement.workshops = [Workshop(6, 6)]

    seed_village_paths(world, settlement)

    assert world.tile_at(8, 6).kind == PATH
    assert world.tile_at(9, 6).kind == "water"


def test_path_border_edges_skip_internal_shared_borders():
    world = make_world(3, 1)
    world.tiles[0][0].kind = PATH
    world.tiles[0][1].kind = DIRT_PATH

    left_edges = path_border_edges(world, 0, 0)
    right_edges = path_border_edges(world, 1, 0)

    assert left_edges["east"] is False
    assert left_edges["west"] is True
    assert right_edges["west"] is False
    assert right_edges["east"] is True


def test_traffic_wear_thresholds_promote_visible_path_stages():
    tile = Tile("grass")

    tile.foot_traffic = PATH_TRAFFIC_TRAMPLED_THRESHOLD
    assert apply_path_wear(tile)
    assert tile.kind == TRAMPLED_GRASS

    tile.foot_traffic = PATH_TRAFFIC_WORN_THRESHOLD
    assert apply_path_wear(tile)
    assert tile.kind == WORN_GRASS

    tile.foot_traffic = PATH_TRAFFIC_DIRT_THRESHOLD
    assert apply_path_wear(tile)
    assert tile.kind == DIRT_PATH

    tile.foot_traffic = PATH_TRAFFIC_ESTABLISHED_THRESHOLD
    assert apply_path_wear(tile)
    assert tile.kind == PATH


def test_repeated_traffic_creates_emergent_path():
    world = make_world(3, 1)

    for _ in range(PATH_TRAFFIC_DIRT_THRESHOLD):
        record_foot_traffic(world, 1, 0)

    assert world.tile_at(1, 0).foot_traffic == PATH_TRAFFIC_DIRT_THRESHOLD
    assert world.tile_at(1, 0).kind == DIRT_PATH


def test_daily_traffic_decay_is_slow_and_can_fade_abandoned_paths():
    world = make_world(3, 1)
    tile = world.tile_at(1, 0)
    tile.foot_traffic = PATH_TRAFFIC_ESTABLISHED_THRESHOLD
    apply_path_wear(tile)

    decay_foot_traffic(world)

    assert tile.foot_traffic == PATH_TRAFFIC_ESTABLISHED_THRESHOLD - PATH_TRAFFIC_DAILY_DECAY
    assert tile.kind == DIRT_PATH

    while tile.foot_traffic > 0:
        decay_foot_traffic(world)

    assert tile.foot_traffic == 0
    assert tile.kind == "grass"
