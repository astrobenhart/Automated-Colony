import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.renderer import PygameRenderer
from src.tile import Tile
from src.world import World, create_world
from src.world_identity import SURVIVAL_OUTLOOKS, generate_world_identity
from src.worldgen_settings import WORLD_PRESETS, WorldGenSettings


def make_world(kinds: list[list[str]], settings: WorldGenSettings | None = None) -> World:
    height = len(kinds)
    width = len(kinds[0])
    world = World(width, height, seed=12, settings=settings or WorldGenSettings(seed=12, width=width, height=height))
    world.tiles = [[Tile(kind) for kind in row] for row in kinds]
    for row in world.tiles:
        for tile in row:
            if tile.kind == "wetland":
                tile.food = 3
            elif tile.kind == "forest":
                tile.wood = 4
                tile.food = 1
    return world


def teardown_function():
    pygame.quit()


def test_world_identity_is_generated_for_created_world():
    world = create_world(settings=WorldGenSettings(seed=44, width=30, height=20), agent_count=0)

    assert world.identity is not None
    assert world.identity.title
    assert world.identity.subtitle
    assert world.identity.survival_outlook in SURVIVAL_OUTLOOKS
    assert world.identity.tags


def test_same_seed_and_settings_produce_same_identity():
    settings = WorldGenSettings(seed=45, width=30, height=20)

    first = create_world(settings=settings, agent_count=0).identity
    second = create_world(settings=settings, agent_count=0).identity

    assert first == second


def test_different_seed_or_settings_can_produce_different_identity():
    first = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=46, width=30, height=20), agent_count=0).identity
    second = create_world(settings=WORLD_PRESETS["harsh"].with_overrides(seed=47, width=30, height=20), agent_count=0).identity

    assert first != second


def test_harsh_settings_produce_harsher_outlook_than_gentle_settings():
    gentle = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=77), agent_count=0).identity
    harsh = create_world(settings=WORLD_PRESETS["harsh"].with_overrides(seed=77), agent_count=0).identity

    assert SURVIVAL_OUTLOOKS.index(harsh.survival_outlook) > SURVIVAL_OUTLOOKS.index(gentle.survival_outlook)


def test_wetland_world_gets_wet_or_marsh_tags():
    world = make_world([
        ["water", "water", "wetland", "wetland"],
        ["water", "wetland", "wetland", "grass"],
        ["plain", "wetland", "wetland", "grass"],
    ])

    identity = generate_world_identity(world)

    assert "wet" in identity.tags
    assert "marshland" in identity.tags


def test_forest_world_gets_forested_tags():
    world = make_world([
        ["forest", "forest", "forest", "plain"],
        ["forest", "forest", "grass", "plain"],
        ["forest", "hill", "grass", "plain"],
    ])

    identity = generate_world_identity(world)

    assert "forested" in identity.tags
    assert "wood_rich" in identity.tags


def test_identity_header_draws_and_keeps_text_compact():
    world = create_world(settings=WorldGenSettings(seed=48, width=30, height=20), agent_count=0)
    renderer = PygameRenderer(world)

    end_y = renderer.draw_world_identity_header(10, 10, 260, 200)

    assert end_y > 10
    assert len(world.identity.title) <= 24
    assert len(world.identity.subtitle) <= 62
