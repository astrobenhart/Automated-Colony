from src.resource_ecology import food_dieoff_chance, food_growth_chance
from src.world import create_world
from src.worldgen_settings import WORLD_PRESETS, WorldGenSettings


def terrain_signature(world):
    return [
        [(tile.kind, tile.food, tile.wood) for tile in row]
        for row in world.tiles
    ]


def count_tiles(world, kind: str) -> int:
    return sum(1 for row in world.tiles for tile in row if tile.kind == kind)


def test_default_settings_create_world_with_default_dimensions():
    world = create_world(settings=WorldGenSettings(seed=10), agent_count=0)

    assert world.width == WorldGenSettings().width
    assert world.height == WorldGenSettings().height
    assert world.settings.seed == 10


def test_same_settings_seed_reproduces_world():
    settings = WorldGenSettings(seed=42, width=30, height=20)

    first = create_world(settings=settings, agent_count=0)
    second = create_world(settings=settings, agent_count=0)

    assert terrain_signature(first) == terrain_signature(second)
    assert [(animal.species, animal.x, animal.y) for animal in first.animals] == [
        (animal.species, animal.x, animal.y) for animal in second.animals
    ]


def test_different_seeds_usually_produce_different_worlds():
    first = create_world(settings=WorldGenSettings(seed=42, width=30, height=20), agent_count=0)
    second = create_world(settings=WorldGenSettings(seed=43, width=30, height=20), agent_count=0)

    assert terrain_signature(first) != terrain_signature(second)


def test_dimensions_follow_settings():
    world = create_world(settings=WorldGenSettings(seed=1, width=17, height=9), agent_count=0)

    assert world.width == 17
    assert world.height == 9
    assert len(world.tiles) == 9
    assert len(world.tiles[0]) == 17


def test_wet_preset_increases_water_coverage():
    normal = create_world(settings=WORLD_PRESETS["normal"].with_overrides(seed=99), agent_count=0)
    wet = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=99), agent_count=0)

    assert count_tiles(wet, "water") > count_tiles(normal, "water")


def test_forest_preset_increases_forest_coverage():
    normal = create_world(settings=WORLD_PRESETS["normal"].with_overrides(seed=99), agent_count=0)
    forest = create_world(settings=WORLD_PRESETS["forest"].with_overrides(seed=99), agent_count=0)

    assert count_tiles(forest, "forest") > count_tiles(normal, "forest")


def test_harsh_preset_changes_ecology_pressure():
    normal = WORLD_PRESETS["normal"]
    harsh = WORLD_PRESETS["harsh"]

    assert food_growth_chance("plain", "Spring", settings=harsh) < food_growth_chance("plain", "Spring", settings=normal)
    assert food_dieoff_chance("plain", "Summer", settings=harsh) > food_dieoff_chance("plain", "Summer", settings=normal)


def test_invalid_settings_are_clamped_or_corrected():
    settings = WorldGenSettings(
        width=-5,
        height=0,
        water_level=9.0,
        forest_density=-4.0,
        climate_harshness=2.0,
        mountain_level=-1.0,
        river_count=-3,
        wildlife_density=8.0,
        event_frequency=-2.0,
        resource_abundance=3.0,
    )

    assert settings.width == 1
    assert settings.height == 1
    assert settings.water_level == 1.0
    assert settings.forest_density == 0.0
    assert settings.climate_harshness == 1.0
    assert settings.mountain_level == 0.0
    assert settings.river_count == 0
    assert settings.wildlife_density == 1.0
    assert settings.event_frequency == 0.0
    assert settings.resource_abundance == 1.0
