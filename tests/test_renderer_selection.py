import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.carrying_capacity import CarryingCapacityReport
from src.config import (
    COLORS,
    DEBUG_DRAW_GRID,
    SYMBOL_LABELS,
    TILE_SIZE,
    TERRAIN_LABELS,
    TICKS_PER_DAY,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from src.renderer import PygameRenderer
from src.renderer import color_for_role
from src.renderer import is_food_visible_to_player
from src.renderer import is_wood_visible_to_player
from src.overlays.villagers import VILLAGERS_OVERLAY
from src.lifecycle import ELDER
from src.roles import BUILDER, FORAGER, GENERALIST, ROLES, SCOUT
from src.seasons import seasonal_tile_color
from src.settlement import Settlement
from src.social_memory import SocialMemoryEntry
from src.state import WORKING
from src.tile import Tile
from src.traits import CURIOUS
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


def test_viewport_is_larger_without_changing_tile_size():
    assert TILE_SIZE == 16
    assert VIEWPORT_WIDTH == 76
    assert VIEWPORT_HEIGHT == 45


def test_adjacent_tiles_draw_without_grid_gap():
    world = make_world(width=2, height=1)
    renderer = make_renderer(world)

    renderer.draw_world()

    boundary_pixel = renderer.screen.get_at((TILE_SIZE, TILE_SIZE // 2))[:3]
    assert boundary_pixel == renderer.tile_color("grass")


def test_selection_highlight_aligns_with_camera_offset():
    world = make_world(width=100, height=60)
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
    assert "r" in SYMBOL_LABELS


def test_legend_swatch_uses_current_seasonal_color():
    world = make_world(width=3, height=3)
    world.season_index = 1
    renderer = make_renderer(world)
    x = 20
    y = 20

    renderer.draw_legend_item("wetland", "Wetland", x, y, 120)

    swatch_pixel = renderer.screen.get_at((x + 1, y + 3))[:3]
    assert swatch_pixel == renderer.tile_color("wetland")


def test_map_and_legend_use_same_seasonal_color_source():
    world = make_world(width=3, height=3)
    world.tiles[0][0] = Tile("wetland")
    world.season_index = 3
    renderer = make_renderer(world)

    renderer.draw_world()
    map_pixel = renderer.screen.get_at((1, 1))[:3]

    renderer.draw_legend_item("wetland", "Wetland", 40, 40, 120)
    legend_pixel = renderer.screen.get_at((41, 43))[:3]

    assert map_pixel == renderer.tile_color("wetland")
    assert legend_pixel == map_pixel


def test_legend_uses_blended_transition_color():
    world = make_world(width=3, height=3)
    world.day = 20
    world.tick = TICKS_PER_DAY // 2
    renderer = make_renderer(world)
    x = 20
    y = 20

    renderer.draw_legend_item("plain", "Plain", x, y, 120)

    swatch_pixel = renderer.screen.get_at((x + 1, y + 3))[:3]
    assert swatch_pixel == renderer.tile_color("plain")
    assert swatch_pixel != seasonal_tile_color("plain", "Spring")
    assert swatch_pixel != seasonal_tile_color("plain", "Summer")


def test_resource_symbol_color_reflects_abundance():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    low_food = renderer.resource_color("food", amount=1, cap=7)
    high_food = renderer.resource_color("food", amount=7, cap=7)

    assert low_food != high_food
    assert sum(high_food) > sum(low_food)


def test_known_food_is_visible_to_player():
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    world.colony_memory.remember_food((1, 1))

    assert is_food_visible_to_player(world, 1, 1)


def test_unknown_food_is_hidden_as_resource(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert not is_food_visible_to_player(world, 1, 1)
    assert not any(symbol == "f" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_known_food_renders_resource_symbol(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    world.colony_memory.remember_food((1, 1))
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert any(symbol == "f" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_forgotten_food_stops_rendering_as_known_resource(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    world.colony_memory.remember_food((1, 1))
    world.colony_memory.forget_food((1, 1))
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert not is_food_visible_to_player(world, 1, 1)
    assert not any(symbol == "f" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_known_wood_is_visible_to_player():
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    world.colony_memory.remember_wood((1, 1))

    assert is_wood_visible_to_player(world, 1, 1)


def test_unknown_wood_is_hidden_as_resource(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert not is_wood_visible_to_player(world, 1, 1)
    assert not any(symbol == "w" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_known_wood_renders_resource_symbol(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    world.colony_memory.remember_wood((1, 1))
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert any(symbol == "w" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_forgotten_wood_stops_rendering_as_known_resource(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    world.colony_memory.remember_wood((1, 1))
    world.colony_memory.forget_wood((1, 1))
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert not is_wood_visible_to_player(world, 1, 1)
    assert not any(symbol == "w" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_terrain_remains_visible_when_food_resource_is_unknown():
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    renderer = make_renderer(world)

    renderer.draw_world()

    terrain_pixel = renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + 1))[:3]
    assert terrain_pixel == renderer.tile_color("grass")


def test_forest_terrain_remains_visible_when_wood_resource_is_unknown():
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    renderer = make_renderer(world)

    renderer.draw_world()

    terrain_pixel = renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + 1))[:3]
    assert terrain_pixel == renderer.tile_color("forest")


def test_resource_visibility_uses_colony_memory_not_agent_personal_memory(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    agent = Agent("Ari", 0, 0)
    agent.remembered_food.add((1, 1))
    world.agents.append(agent)
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert not is_food_visible_to_player(world, 1, 1)
    assert not any(symbol == "f" and x == 1 and y == 1 for symbol, x, y, _ in calls)


def test_selected_tile_resource_details_hide_unknown_quantities(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 3
    renderer = make_renderer(world)
    renderer.selected_tile = (1, 1)
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Food", "Unknown") in rows
    assert ("Wood", "Unknown") in rows
    assert ("Terrain", "forest") in rows


def test_selected_tile_resource_details_show_known_quantities(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1].food = 2
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 3
    world.colony_memory.remember_food((1, 1))
    world.colony_memory.remember_wood((1, 1))
    renderer = make_renderer(world)
    renderer.selected_tile = (1, 1)
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Food", 2) in rows
    assert ("Wood", 3) in rows


def test_every_known_role_maps_to_a_color():
    for role in ROLES:
        color = color_for_role(role)

        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= channel <= 255 for channel in color)


def test_known_role_colors_are_distinct():
    colors = [color_for_role(role) for role in ROLES]

    assert len(set(colors)) == len(ROLES)


def test_unknown_role_uses_safe_fallback_color():
    assert color_for_role("Mystery Role") == COLORS["agent"]
    assert color_for_role(None) == COLORS["agent"]


def test_role_color_lookup_is_deterministic():
    assert color_for_role(FORAGER) == color_for_role(FORAGER)


def test_renderer_draws_agent_using_role_color(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Bryn", 1, 1, role=BUILDER)
    world.agents.append(agent)
    renderer = make_renderer(world)
    calls = []

    def spy_draw_centered_symbol(symbol, x, y, color):
        calls.append((symbol, x, y, color))

    monkeypatch.setattr(renderer, "draw_centered_symbol", spy_draw_centered_symbol)

    renderer.draw_world()

    assert ("@", 1, 1, color_for_role(BUILDER)) in calls


def test_role_colors_are_bright_for_screensaver_readability():
    for role in (GENERALIST, FORAGER, BUILDER, SCOUT):
        color = color_for_role(role)

        assert max(color) >= 175
        assert sum(color) >= 330


def test_selected_agent_details_include_lifecycle_stage(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Eli", 1, 1, lifecycle_stage=ELDER)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.selected_agent = agent
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Life", ELDER) in rows


def test_selected_agent_details_include_trait(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Cato", 1, 1, trait=CURIOUS)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.selected_agent = agent
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Trait", CURIOUS) in rows


def test_selected_agent_details_include_state(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Dara", 1, 1, current_action="Building shelter")
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.selected_agent = agent
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("State", WORKING) in rows


def test_selected_agent_details_include_familiarity_summary(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Dara", 1, 1)
    agent.social_memory["bryn"] = SocialMemoryEntry(
        villager_id="bryn",
        display_name="Bryn",
        familiarity_score=30,
        last_seen_day=30,
    )
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.selected_agent = agent
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Knows", "Bryn (Familiar)") in rows


def test_history_summary_draws_without_crashing():
    world = make_world(width=3, height=3)
    world.history.record(
        day=3,
        year=1,
        season="Spring",
        category="ENVIRONMENT",
        title="Heavy Rain Begins",
        description="Heavy rain soaks the soil.",
    )
    renderer = make_renderer(world)

    end_y = renderer.draw_history_summary(10, 10, 220, 200)

    assert end_y > 10


def test_panel_column_layout_uses_non_overlapping_equal_columns():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    left_x, left_width, right_x, right_width = renderer.panel_column_layout(20, 300)

    assert left_x == 20
    assert left_width == right_width
    assert left_x + left_width < right_x
    assert right_x + right_width == 320


def test_two_column_status_section_draws_both_columns_compactly():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    end_y = renderer.draw_two_column_section(
        "Simulation",
        [("Day", 4), ("Season", "Spring")],
        "Colony",
        [("Living", 2), ("Food", 5)],
        10,
        10,
        300,
        220,
    )

    assert end_y > 10


def test_time_grid_contains_day_year_season_and_speed():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    rows = renderer.time_grid_rows(sim_speed=4)

    assert rows == [
        ("Day", world.day),
        ("Year", world.year),
        ("Season", world.season_label),
        ("Speed", "4x"),
    ]


def test_colony_summary_uses_villagers_without_capacity_denominator():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent(f"A{i}", i, 1) for i in range(9)]
    world.settlement.carrying_capacity_report = CarryingCapacityReport(
        population=9,
        capacity=12,
        status="Stable",
        reason="Current shelter, food, and water can support the living population.",
    )
    renderer = make_renderer(world)

    lines = renderer.colony_summary_lines()
    summary = "\n".join(lines)

    assert "9 Villagers" in lines
    assert "9 / 12 Villagers" not in summary
    assert "9/12" not in summary


def test_colony_summary_excludes_debug_fields():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent("Ari", 1, 1)]
    world.settlement.carrying_capacity_report = CarryingCapacityReport(
        population=1,
        capacity=3,
        status="Stable",
        reason="Current shelter, food, and water can support the living population.",
    )
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Center" not in summary
    assert "Rad" not in summary
    assert "Claims" not in summary
    assert "Cap" not in summary
    assert "Settle" not in summary


def test_colony_reason_lines_are_capped_and_hidden_when_stable():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent(f"A{i}", i, 1) for i in range(9)]
    world.settlement.carrying_capacity_report = CarryingCapacityReport(
        population=9,
        capacity=6,
        status="Food Strained",
        reason="Food is the limiting factor.",
    )
    renderer = make_renderer(world)

    assert len(renderer.colony_reason_lines(max_lines=2)) == 2

    world.settlement.carrying_capacity_report = CarryingCapacityReport(
        population=9,
        capacity=12,
        status="Stable",
        reason="Current shelter, food, and water can support the living population.",
    )

    assert renderer.colony_reason_lines() == []


def test_colony_summary_handles_missing_capacity_report():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    renderer = make_renderer(world)

    lines = renderer.colony_summary_lines()

    assert "Unknown" in lines


def test_renderer_recognizes_settlement_center():
    world = make_world(width=5, height=5)
    world.settlement = Settlement("Willowhold", 2, 3, founded_day=1, founded_season="Spring")
    renderer = make_renderer(world)

    assert renderer.is_settlement_center(2, 3)
    assert not renderer.is_settlement_center(3, 2)


def test_renderer_toggles_villagers_overlay_without_duplicates():
    world = make_world(width=5, height=5)
    world.agents = [Agent("Ari", 1, 1)]
    renderer = make_renderer(world)

    renderer.toggle_villagers_overlay()
    first_overlay = renderer.overlay_manager.active[VILLAGERS_OVERLAY]

    renderer.toggle_villagers_overlay()

    assert not renderer.overlay_manager.is_open(VILLAGERS_OVERLAY)

    renderer.toggle_villagers_overlay()

    assert renderer.overlay_manager.is_open(VILLAGERS_OVERLAY)
    assert renderer.overlay_manager.active[VILLAGERS_OVERLAY] is not first_overlay
    assert len(renderer.overlay_manager.active) == 1


def test_renderer_set_world_closes_active_overlays():
    renderer = make_renderer(make_world(width=5, height=5))
    renderer.world.agents = [Agent("Ari", 1, 1)]
    renderer.toggle_villagers_overlay()

    renderer.set_world(make_world(width=5, height=5))

    assert not renderer.overlay_manager.is_open(VILLAGERS_OVERLAY)
