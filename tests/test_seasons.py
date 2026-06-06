from src.config import DAYS_PER_SEASON, SEASONS, TERRAIN_LABELS, TICKS_PER_DAY
from src.seasons import (
    food_growth_chance,
    lerp_color,
    seasonal_tile_color,
    transition_progress,
    wood_growth_chance,
)
from src.tile import Tile
from src.world import World, create_world


def make_world_with_tiles(kinds):
    height = len(kinds)
    width = len(kinds[0])
    world = World(width, height)
    world.tiles = [[Tile(kind) for kind in row] for row in kinds]
    return world


def test_world_starts_with_valid_season():
    world = make_world_with_tiles([["grass"]])

    assert world.season == "Spring"
    assert world.season in SEASONS
    assert world.day_of_season == 1


def test_season_length_is_twenty_days():
    assert DAYS_PER_SEASON == 20


def test_seasons_advance_after_configured_number_of_days():
    world = make_world_with_tiles([["grass"]])
    world.day = DAYS_PER_SEASON

    world.advance_day()

    assert world.season == "Summer"
    assert world.day_of_season == 1


def test_season_advancement_wraps_from_winter_to_spring():
    world = make_world_with_tiles([["grass"]])
    world.season_index = SEASONS.index("Winter")
    world.day = DAYS_PER_SEASON

    world.advance_day()

    assert world.season == "Spring"


def test_season_changes_are_logged():
    world = make_world_with_tiles([["grass"]])
    world.day = DAYS_PER_SEASON

    world.advance_day()

    assert any("Summer begins." in event for event in world.events)


def test_spring_and_autumn_food_growth_are_stronger_than_winter():
    assert food_growth_chance("plain", "Spring") > food_growth_chance("plain", "Winter")
    assert food_growth_chance("plain", "Autumn") > food_growth_chance("plain", "Winter")


def test_terrain_affects_seasonal_food_regrowth():
    spring = "Spring"

    assert food_growth_chance("wetland", spring) > food_growth_chance("plain", spring)
    assert food_growth_chance("forest", spring) > food_growth_chance("dry", spring)
    assert food_growth_chance("dry", spring) > food_growth_chance("mountain", spring)
    assert food_growth_chance("mountain", spring) == 0.0
    assert food_growth_chance("water", spring) == 0.0


def test_wood_regrowth_stays_forest_focused():
    assert wood_growth_chance("forest", "Spring") > wood_growth_chance("hill", "Spring")
    assert wood_growth_chance("plain", "Spring") == 0.0
    assert wood_growth_chance("water", "Spring") == 0.0


def test_water_remains_water_after_season_advancement():
    world = make_world_with_tiles([["water", "forest"], ["plain", "dry"]])
    world.day = DAYS_PER_SEASON

    world.advance_day()

    assert world.tile_at(0, 0).kind == "water"
    assert not world.tile_at(0, 0).walkable


def test_transition_progress_only_runs_during_final_season_day():
    assert transition_progress(DAYS_PER_SEASON - 1, TICKS_PER_DAY - 1, TICKS_PER_DAY) == 0.0
    assert transition_progress(DAYS_PER_SEASON, 0, TICKS_PER_DAY) == 0.0
    assert transition_progress(DAYS_PER_SEASON, TICKS_PER_DAY // 2, TICKS_PER_DAY) > 0.0


def test_transition_progress_reaches_one_at_season_boundary():
    assert transition_progress(DAYS_PER_SEASON, TICKS_PER_DAY - 1, TICKS_PER_DAY) == 1.0


def test_lerp_color_returns_expected_midpoint():
    assert lerp_color((10, 20, 30), (30, 40, 50), 0.5) == (20, 30, 40)


def test_seasonal_color_lookup_varies_terrain_across_seasons():
    assert seasonal_tile_color("wetland", "Spring") != seasonal_tile_color("wetland", "Winter")
    assert seasonal_tile_color("forest", "Spring") != seasonal_tile_color("forest", "Autumn")
    assert seasonal_tile_color("water", "Spring") != seasonal_tile_color("water", "Summer")


def test_blended_color_differs_from_both_endpoints():
    spring = seasonal_tile_color("wetland", "Spring")
    summer = seasonal_tile_color("wetland", "Summer")
    blended = seasonal_tile_color("wetland", "Spring", "Summer", 0.5)

    assert blended != spring
    assert blended != summer


def test_seasonal_color_lookup_handles_all_terrain_labels():
    for season in SEASONS:
        for terrain in TERRAIN_LABELS:
            color = seasonal_tile_color(terrain, season)

            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= channel <= 255 for channel in color)


def test_visual_seasonal_effects_do_not_change_tile_kind():
    tile = Tile("wetland")

    for season in SEASONS:
        seasonal_tile_color(tile.kind, season)

    assert tile.kind == "wetland"
    assert tile.walkable


def test_world_exposes_visual_transition_state():
    world = make_world_with_tiles([["grass"]])
    world.day = DAYS_PER_SEASON
    world.tick = TICKS_PER_DAY // 2

    assert world.season == "Spring"
    assert world.next_season == "Summer"
    assert world.transition_progress > 0.0
    assert world.season_label == "Spring -> Summer"


def test_rivers_and_permanent_water_remain_valid_water_sources_after_seasons():
    world = create_world(seed=31, agent_count=0)
    river_tiles = {pos for path in world.river_paths for pos in path}
    starting_water = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == "water"
    }

    assert river_tiles
    assert river_tiles.issubset(starting_water)

    for _ in range(DAYS_PER_SEASON * len(SEASONS)):
        world.advance_day()

    ending_water = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.kind == "water"
    }

    assert starting_water == ending_water
    assert all(world.tile_at(x, y).kind == "water" for x, y in river_tiles)
