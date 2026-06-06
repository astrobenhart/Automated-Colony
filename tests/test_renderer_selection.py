import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.config import TILE_SIZE
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
