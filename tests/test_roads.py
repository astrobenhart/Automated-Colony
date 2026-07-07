from src.config import PATH_TRAFFIC_DAILY_DECAY, PATH_TRAFFIC_ESTABLISHED_THRESHOLD
from src.settlement import Settlement
from src.tile import Tile
from src.village_paths import (
    PATH,
    ROAD_ORIGIN_WORLD,
    apply_path_wear,
    decay_foot_traffic,
    is_permanent_world_road,
)
from src.wanderers import ARRIVING, advance_wanderer, spawn_wanderer
from src.world import World
from src.world_roads import seed_main_roads


def make_world(width: int = 24, height: int = 24) -> World:
    world = World(width, height, seed=6161)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", width // 2, height // 2, 1, "Spring", settlement_id="oakvale")
    seed_main_roads(world, world.settlement)
    return world


def test_world_generated_roads_are_marked_as_permanent_world_roads():
    world = make_world()

    for road in world.main_roads:
        road_tiles = [world.tile_at(x, y) for x, y in road.path if world.tile_at(x, y).kind == PATH]

        assert road_tiles
        assert all(tile.road_origin == ROAD_ORIGIN_WORLD for tile in road_tiles)
        assert all(is_permanent_world_road(tile) for tile in road_tiles)


def test_world_generated_roads_do_not_decay():
    world = make_world()
    road = world.main_roads[0]
    road_tile = next(world.tile_at(x, y) for x, y in road.path if world.tile_at(x, y).kind == PATH)
    starting_traffic = road_tile.foot_traffic

    for _ in range(starting_traffic + PATH_TRAFFIC_DAILY_DECAY + 5):
        decay_foot_traffic(world)

    assert road_tile.foot_traffic == starting_traffic
    assert road_tile.kind == PATH
    assert road_tile.road_origin == ROAD_ORIGIN_WORLD


def test_villager_created_paths_continue_decaying_normally():
    world = make_world()
    tile = Tile("grass")
    tile.foot_traffic = PATH_TRAFFIC_ESTABLISHED_THRESHOLD
    apply_path_wear(tile)
    world.tiles[1][1] = tile

    decay_foot_traffic(world)

    assert tile.foot_traffic == PATH_TRAFFIC_ESTABLISHED_THRESHOLD - PATH_TRAFFIC_DAILY_DECAY
    assert tile.road_origin is None
    assert tile.kind != PATH


def test_wanderers_continue_using_permanent_world_roads():
    world = make_world()
    road = world.main_roads[0]
    wanderer = spawn_wanderer(world, profile_id="pilgrim", road_index=0)

    assert wanderer.visitor_status == ARRIVING
    assert wanderer.visitor_path == list(reversed(road.path))
    assert world.tile_at(*wanderer.visitor_path[0]).road_origin == ROAD_ORIGIN_WORLD

    advance_wanderer(world, wanderer)

    assert (wanderer.x, wanderer.y) in set(road.path)
    assert world.tile_at(wanderer.x, wanderer.y).road_origin == ROAD_ORIGIN_WORLD
