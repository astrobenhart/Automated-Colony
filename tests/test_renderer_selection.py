import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.config import (
    COLORS,
    DEBUG_DRAW_GRID,
    SYMBOL_LABELS,
    TILE_SIZE,
    TERRAIN_LABELS,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from src.renderer import PygameRenderer
from src.tile import Tile
from src.world import World


def make_world(width: int = 3, height: int = 3) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def make_renderer(world: World) -> PygameRenderer:
    return PygameRenderer(world)


def teardown_function():
    pygame.quit()


def test_clicking_agent_selects_agent():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    renderer = make_renderer(world)

    renderer.select_tile_at_pixel(1 * TILE_SIZE + 2, 1 * TILE_SIZE + 2)

    assert renderer.selected_agent is agent
    assert renderer.selected_tile is None


def test_clicking_empty_tile_selects_tile():
    world = make_world()
    renderer = make_renderer(world)

    renderer.select_tile_at_pixel(2 * TILE_SIZE + 2, 1 * TILE_SIZE + 2)

    assert renderer.selected_agent is None
    assert renderer.selected_tile == (2, 1)


def test_selection_is_read_only():
    world = make_world()
    agent = Agent("Ari", 1, 1, hunger=10, thirst=20, fatigue=30)
    world.agents.append(agent)
    renderer = make_renderer(world)

    renderer.select_tile(1, 1)

    assert (agent.x, agent.y) == (1, 1)
    assert agent.hunger == 10
    assert agent.thirst == 20
    assert agent.fatigue == 30
    assert agent.current_action == "Idle"
    assert agent.current_goal == "Explore"


def test_restart_world_clears_stale_agent_selection():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.select_tile(1, 1)

    renderer.world = make_world()
    renderer.validate_selection()

    assert renderer.selected_agent is None
    assert renderer.selected_tile is None


def test_dead_agent_selection_does_not_crash_draw():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.select_tile(1, 1)

    agent.alive = False

    renderer.draw(paused=False, sim_speed=1)

    assert renderer.selected_agent is agent


def test_fit_text_truncates_to_available_width():
    world = make_world()
    renderer = make_renderer(world)

    text = renderer.fit_text(
        "Day 4: Ari died of starvation after a very long diagnostic message",
        renderer.font,
        120,
    )

    assert text.endswith("...")
    assert renderer.font.size(text)[0] <= 120


def test_draw_text_line_stops_before_panel_bottom():
    world = make_world()
    renderer = make_renderer(world)
    start_y = 100
    bottom_y = start_y + renderer.font.get_height() - 1

    end_y = renderer.draw_text_line("Too low", 0, start_y, 120, bottom_y)

    assert end_y == start_y


def test_camera_coordinate_conversion_accounts_for_offset():
    world = make_world(width=80, height=45)
    renderer = make_renderer(world)
    renderer.camera_x = 10
    renderer.camera_y = 5

    tile = renderer.screen_to_world_tile(2 * TILE_SIZE + 1, 3 * TILE_SIZE + 1)

    assert tile == (12, 8)


def test_clicking_panel_clears_selection_instead_of_selecting_hidden_tile():
    world = make_world(width=80, height=45)
    renderer = make_renderer(world)
    renderer.select_tile(1, 1)

    renderer.select_tile_at_pixel(VIEWPORT_WIDTH * TILE_SIZE + 10, 10)

    assert renderer.selected_agent is None
    assert renderer.selected_tile is None


def test_mouse_selection_accounts_for_camera_offset():
    world = make_world(width=80, height=45)
    agent = Agent("Ari", 12, 8)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.camera_x = 10
    renderer.camera_y = 5

    renderer.select_tile_at_pixel(2 * TILE_SIZE + 2, 3 * TILE_SIZE + 2)

    assert renderer.selected_agent is agent
    assert renderer.selected_tile is None


def test_visible_tile_bounds_stay_inside_world():
    world = make_world(width=80, height=45)
    renderer = make_renderer(world)

    renderer.pan_camera(999, 999)
    start_x, start_y, end_x, end_y = renderer.visible_tile_bounds()

    assert 0 <= start_x < end_x <= world.width
    assert 0 <= start_y < end_y <= world.height
    assert end_x - start_x <= VIEWPORT_WIDTH
    assert end_y - start_y <= VIEWPORT_HEIGHT


def test_tiles_are_smaller_and_grid_is_disabled_by_default():
    assert TILE_SIZE == 16
    assert not DEBUG_DRAW_GRID


def test_adjacent_tiles_draw_without_grid_gap():
    world = make_world(width=2, height=1)
    renderer = make_renderer(world)

    renderer.draw_world()

    boundary_pixel = renderer.screen.get_at((TILE_SIZE, TILE_SIZE // 2))[:3]
    assert boundary_pixel == COLORS["grass"]


def test_selection_highlight_aligns_with_camera_offset():
    world = make_world(width=80, height=45)
    renderer = make_renderer(world)
    renderer.camera_x = 10
    renderer.camera_y = 5
    renderer.select_tile(12, 8)

    renderer.draw_world()

    highlight_pixel = renderer.screen.get_at((2 * TILE_SIZE, 3 * TILE_SIZE))[:3]
    assert highlight_pixel == COLORS["selection"]


def test_legend_draws_terrain_swatch_and_symbol_labels():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    renderer.draw_panel(paused=False, sim_speed=1)

    assert "water" in TERRAIN_LABELS
    assert "@" in SYMBOL_LABELS
