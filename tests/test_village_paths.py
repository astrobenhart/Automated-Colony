from src.settlement import Home, Settlement, Stockpile
from src.tile import Tile
from src.village_paths import PATH, path_border_edges, seed_village_paths
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
    world.tiles[0][1].kind = PATH

    left_edges = path_border_edges(world, 0, 0)
    right_edges = path_border_edges(world, 1, 0)

    assert left_edges["east"] is False
    assert left_edges["west"] is True
    assert right_edges["west"] is False
    assert right_edges["east"] is True
