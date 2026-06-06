from src.config import DAYS_PER_SEASON, SEASONS
from src.seasons import food_growth_chance, wood_growth_chance
from src.tile import Tile
from src.world import World


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
