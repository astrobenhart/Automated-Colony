import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.appearance import appearance_for_seed, appearance_seed_for, appearance_type_for_seed
from src.lifecycle import ADULT, ELDER
from src.portraits import (
    DISPLAY_SIZE,
    ELDER_HAIR,
    clear_portrait_cache,
    draw_character_sprite_surface,
    generate_villager_portrait,
    generate_villager_sprite,
    portrait_appearance_for,
    portrait_layer_metadata,
    portrait_seed_for,
    sprite_layer_metadata,
)
from src.role_colors import color_for_role
from src.roles import BUILDER, FORAGER
from src.world import create_world


def setup_function():
    pygame.init()
    clear_portrait_cache()


def teardown_function():
    pygame.quit()


def test_appearance_seed_is_deterministic():
    assert appearance_seed_for(123, 2, "Ari") == appearance_seed_for(123, 2, "Ari")
    assert appearance_seed_for(123, 2, "Ari") != appearance_seed_for(123, 3, "Ari")


def test_same_villager_produces_same_appearance_metadata():
    agent = Agent(
        "Ari",
        1,
        1,
        appearance_seed=42,
        appearance_type=appearance_type_for_seed(42),
    )

    assert portrait_seed_for(agent) == 42
    assert portrait_appearance_for(agent) == portrait_appearance_for(agent)


def test_world_spawn_assigns_stable_appearance_for_fixed_seed():
    world_a = create_world(width=20, height=20, agent_count=4, seed=77)
    world_b = create_world(width=20, height=20, agent_count=4, seed=77)

    appearances_a = [(agent.appearance_seed, agent.appearance_type) for agent in world_a.agents]
    appearances_b = [(agent.appearance_seed, agent.appearance_type) for agent in world_b.agents]

    assert appearances_a == appearances_b
    assert all(seed is not None and appearance_type is not None for seed, appearance_type in appearances_a)


def test_role_clothing_uses_shared_role_color():
    agent = Agent("Bryn", 1, 1, role=BUILDER, appearance_seed=12)

    metadata = portrait_layer_metadata(agent)
    surface = draw_character_sprite_surface(agent)

    assert metadata["clothing"] == color_for_role(BUILDER)
    assert surface.get_at((13, 18))[:3] == color_for_role(BUILDER)


def test_elder_portrait_hair_differs_from_adult():
    adult = Agent("Ari", 1, 1, lifecycle_stage=ADULT, appearance_seed=42)
    elder = Agent("Ari", 1, 1, lifecycle_stage=ELDER, appearance_seed=42)

    assert portrait_layer_metadata(adult)["hair"] != portrait_layer_metadata(elder)["hair"]
    assert portrait_layer_metadata(elder)["hair"] == ELDER_HAIR


def test_different_appearance_seeds_create_different_metadata():
    first = appearance_for_seed(1)
    second = appearance_for_seed(2)

    assert first != second


def test_portrait_generation_handles_missing_optional_fields_safely():
    villager = SimpleNamespace(name="Mystery")

    surface = generate_villager_portrait(villager)

    assert surface.get_size() == (DISPLAY_SIZE, DISPLAY_SIZE)


def test_portrait_generation_is_cached():
    agent = Agent("Dara", 1, 1, role=FORAGER, appearance_seed=99)

    first = generate_villager_portrait(agent)
    second = generate_villager_portrait(agent)

    assert first is second


def test_character_sprite_has_full_body_rpg_proportions():
    agent = Agent("Dara", 1, 1, role=FORAGER, appearance_seed=99)

    surface = draw_character_sprite_surface(agent)

    assert surface.get_at((16, 13))[:3] == sprite_layer_metadata(agent)["skin"]
    assert surface.get_at((13, 18))[:3] == color_for_role(FORAGER)
    assert surface.get_at((11, 26))[:3] != color_for_role(FORAGER)
    assert surface.get_at((11, 26))[:3] != sprite_layer_metadata(agent)["skin"]


def test_sprite_alias_uses_same_cached_surface_as_portrait_api():
    agent = Agent("Eli", 1, 1, role=BUILDER, appearance_seed=123)

    assert generate_villager_sprite(agent) is generate_villager_portrait(agent)
