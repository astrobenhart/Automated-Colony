from src.actions import BuildShelterAction, SeekBuildSiteAction
from src.agent import Agent
from src.building_placement import (
    find_build_site_near_settlement,
    is_buildable_tile,
    score_build_site,
    would_block_access,
)
from src.building_priorities import SHELTER
from src.roles import BUILDER
from src.settlement import FOOD, WOOD, Settlement, Stockpile, distance_to_settlement
from src.tile import Tile
from src.workshop import Workshop
from src.world import World


def make_world(width=15, height=15):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement(
        "Willowhold",
        width // 2,
        height // 2,
        1,
        "Spring",
        radius=4,
        stockpiles=[
            Stockpile(width // 2, width // 2 + 1, FOOD),
            Stockpile(width // 2 + 1, width // 2, WOOD),
        ],
        workshops=[Workshop(width // 2 - 1, height // 2)],
    )
    return world


def test_is_buildable_tile_rejects_water_and_mountain():
    world = make_world()
    world.tile_at(3, 3).kind = "water"
    world.tile_at(4, 4).kind = "mountain"

    assert not is_buildable_tile(world, 3, 3, SHELTER)
    assert not is_buildable_tile(world, 4, 4, SHELTER)


def test_is_buildable_tile_rejects_occupied_and_special_tiles():
    world = make_world()
    settlement = world.settlement
    agent = Agent("Ari", 3, 3)
    world.agents.append(agent)

    assert not is_buildable_tile(world, 3, 3, SHELTER)
    assert not is_buildable_tile(world, settlement.x, settlement.y, SHELTER)
    assert not is_buildable_tile(world, settlement.stockpiles[0].x, settlement.stockpiles[0].y, SHELTER)
    assert not is_buildable_tile(world, settlement.workshops[0].x, settlement.workshops[0].y, SHELTER)


def test_score_build_site_prefers_tiles_near_settlement():
    world = make_world(width=20, height=20)

    near_score = score_build_site(world, 12, 10, SHELTER)
    far_score = score_build_site(world, 17, 10, SHELTER)

    assert near_score < far_score


def test_score_build_site_prefers_reasonable_shelter_spacing():
    world = make_world()
    world.tile_at(8, 7).kind = "shelter"

    adjacent_score = score_build_site(world, 9, 7, SHELTER)
    spaced_score = score_build_site(world, 10, 7, SHELTER)

    assert spaced_score < adjacent_score


def test_score_build_site_penalizes_overcrowded_shelter_clusters():
    world = make_world()
    for x, y in [(6, 6), (7, 6), (8, 6), (6, 7)]:
        world.tile_at(x, y).kind = "shelter"

    crowded_score = score_build_site(world, 7, 7, SHELTER)
    loose_score = score_build_site(world, 9, 8, SHELTER)

    assert loose_score < crowded_score


def test_placement_avoids_stockpile_workshop_and_settlement_center_tiles():
    world = make_world()

    site = find_build_site_near_settlement(world, SHELTER)
    special_positions = {
        (world.settlement.x, world.settlement.y),
        *{(stockpile.x, stockpile.y) for stockpile in world.settlement.stockpiles},
        *{(workshop.x, workshop.y) for workshop in world.settlement.workshops},
    }

    assert site is not None
    assert site not in special_positions


def test_placement_falls_back_to_broader_bounded_search_when_local_sites_are_blocked():
    world = make_world(width=12, height=12)
    world.settlement = Settlement("Willowhold", 6, 6, 1, "Spring", radius=1)
    for y in range(5, 8):
        for x in range(5, 8):
            world.tile_at(x, y).kind = "mountain"
    world.tile_at(6, 6).kind = "grass"
    world.tile_at(8, 6).kind = "grass"

    site = find_build_site_near_settlement(world, SHELTER)

    assert site is not None
    assert distance_to_settlement(world, site[0], site[1]) > world.settlement.radius
    assert distance_to_settlement(world, site[0], site[1]) <= world.settlement.radius + 4


def test_shelter_construction_uses_placement_helper():
    world = make_world()
    site = find_build_site_near_settlement(world, SHELTER)
    agent = Agent("Builder", site[0], site[1], wood=3, role=BUILDER)
    world.agents.append(agent)

    assert BuildShelterAction().can_do(agent, world)

    BuildShelterAction().execute(agent, world)

    assert world.tile_at(site[0], site[1]).kind == "shelter"


def test_builder_seeks_placement_helper_site_before_building_elsewhere():
    world = make_world()
    site = find_build_site_near_settlement(world, SHELTER)
    agent = Agent("Builder", 0, 0, wood=3, role=BUILDER)
    world.agents.append(agent)

    assert not BuildShelterAction().can_do(agent, world)
    assert SeekBuildSiteAction().can_do(agent, world)

    SeekBuildSiteAction().execute(agent, world)

    assert agent.current_target == site


def test_placement_helper_does_not_call_pathfinding(monkeypatch):
    world = make_world()

    def fail_find_path(*args, **kwargs):
        raise AssertionError("building placement scoring must not pathfind")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    assert find_build_site_near_settlement(world, SHELTER) is not None


def test_clustered_shelters_appear_within_settlement_radius_under_normal_conditions():
    world = make_world(width=18, height=18)
    settlement = world.settlement
    built = []

    for _ in range(3):
        site = find_build_site_near_settlement(world, SHELTER)
        assert site is not None
        world.tile_at(site[0], site[1]).kind = "shelter"
        built.append(site)

    assert all(distance_to_settlement(world, x, y) <= settlement.radius for x, y in built)
    assert any(
        1 <= max(abs(x - ox), abs(y - oy)) <= 3
        for index, (x, y) in enumerate(built)
        for ox, oy in built[index + 1:]
    )


def test_would_block_access_flags_tight_chokepoints():
    world = make_world(width=7, height=7)
    world.settlement = Settlement("Willowhold", 3, 3, 1, "Spring", radius=3)
    world.tile_at(2, 3).kind = "mountain"
    world.tile_at(4, 3).kind = "mountain"
    world.tile_at(3, 2).kind = "mountain"

    assert would_block_access(world, 3, 4)
