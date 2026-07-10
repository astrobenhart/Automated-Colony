import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.carrying_capacity import CarryingCapacityReport
from src.config import (
    COLORS,
    DEBUG_DRAW_GRID,
    DAYS_PER_SEASON,
    FOREST_SEASON_TRANSITION_DAYS,
    GRASS_MOISTURE_TRANSITION_HOURS,
    RENDER_DETAIL_HIGH,
    RENDER_DETAIL_LOW,
    RENDER_DETAIL_MEDIUM,
    RENDER_DETAIL_ULTRA,
    TERRAIN_RENDER_DETAIL,
    TILE_SIZE,
    TICKS_PER_HOUR,
    TERRAIN_LABELS,
    TICKS_PER_DAY,
    WATER_WEATHER_TRANSITION_HOURS,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from src.environment_events import create_environment_event
from src.renderer import PHASE_BAR_COLORS, PygameRenderer, VILLAGER_TILE_OFFSETS
from src.renderer import color_for_role
from src.renderer import is_food_visible_to_player
from src.renderer import is_wood_visible_to_player
from src.forest_rendering import (
    FOREST_SEASON_PALETTES,
    forest_subcell_colors,
    forest_transition_day,
    forest_visual_season,
)
from src.grass_rendering import (
    DRY,
    GRASS_MOISTURE_PALETTES,
    HEAVY_RAIN as GRASS_HEAVY_RAIN,
    NORMAL,
    WET,
    GrassMoistureTransitionState,
    grass_moisture_state,
    grass_subcell_colors,
    grass_transition_tick,
    grass_visual_moisture_mode,
)
from src.overlays.villagers import VILLAGERS_OVERLAY
from src.roles import BUILDER, FORAGER, GENERALIST, ROLES, SCOUT
from src.seasons import seasonal_tile_color
from src.settlement import Settlement
from src.farming import FIELD_DORMANT, FIELD_GROWING, FIELD_PLANTED, FIELD_READY, FIELD_UNPREPARED, FarmPlot
from src.terrain_rendering import (
    CONSTRUCTION_PALETTES,
    FARM_STAGE_PALETTES,
    MASTER_VEGETATION_PALETTES,
    MICROTILE_RESOLUTION_BY_DETAIL,
    PATH_PALETTES,
    AmbientTerrainOcclusion,
    GameplayVisualState,
    MicrotilePattern,
    MicrotileGrid,
    PathForestEncroachment,
    TerrainNeighbourhood,
    TerrainRenderContext,
    TerrainPaletteManager,
    TerrainRenderer,
    TerrainVisualModifier,
    TERRAIN_TRANSITION_PRIORITY,
    construction_visual_stage,
    crop_visual_stage,
    farm_stage_palette,
    palette_spread,
)
from src.renderer_config import DEFAULT_RENDERER_CONFIG_PATH, load_renderer_art_config
from src.tile import Tile
from src.village_paths import DIRT_PATH, PATH, TRAMPLED_GRASS, WORN_GRASS
from src.water_rendering import (
    CLEAR,
    HEAVY_RAIN,
    RAIN,
    WATER_WEATHER_PALETTES,
    WaterTransitionState,
    water_subcell_colors,
    water_transition_tick,
    water_visual_weather,
    weather_state_for_events,
)
from src.world import World, create_world


def make_world(width: int = 3, height: int = 3) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def make_renderer(world: World) -> PygameRenderer:
    return PygameRenderer(world)


def _test_color_distance(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _test_brightness(color) -> int:
    return color[0] + color[1] + color[2]


def _average_test_color(palette):
    count = len(palette)
    return (
        round(sum(color[0] for color in palette) / count),
        round(sum(color[1] for color in palette) / count),
        round(sum(color[2] for color in palette) / count),
    )


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


def test_renderer_screen_conversion_uses_observer_camera():
    world = make_world(width=80, height=45)
    renderer = make_renderer(world)
    renderer.observer_camera.set_position(7.5, 4.25, snap=True, clamp=False)

    tile = renderer.screen_to_world_tile(TILE_SIZE, TILE_SIZE)

    assert tile == (8, 5)


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
    assert boundary_pixel != COLORS["grid"]
    assert boundary_pixel in renderer.terrain_renderer.microtile_colors_for(renderer.terrain_render_context(1, 0))


def test_selection_highlight_aligns_with_camera_offset():
    world = make_world(width=100, height=60)
    renderer = make_renderer(world)
    renderer.camera_x = 10
    renderer.camera_y = 5
    renderer.select_tile(12, 8)

    renderer.draw_world()

    highlight_pixel = renderer.screen.get_at((2 * TILE_SIZE, 3 * TILE_SIZE))[:3]
    assert highlight_pixel == COLORS["selection"]


def test_tile_inspector_draws_empty_state_when_no_tile_is_available(monkeypatch):
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)
    lines = []

    monkeypatch.setattr(renderer, "hovered_world_tile", lambda: None)

    def spy_draw_text_line(text, x, y, width, bottom_y, font=None, color=None):
        lines.append(text)
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_text_line", spy_draw_text_line)

    renderer.draw_tile_inspector(0, 0, 200, 200)

    assert "Hover over a tile to inspect it." in lines


def test_tile_inspector_uses_selected_tile_before_hover(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[1][1] = Tile("water")
    world.tiles[2][2] = Tile("forest")
    renderer = make_renderer(world)
    renderer.selected_tile = (1, 1)
    monkeypatch.setattr(renderer, "hovered_world_tile", lambda: (2, 2))

    rows = renderer.tile_inspector_rows(1, 1)

    assert ("Terrain", TERRAIN_LABELS["water"]) in rows
    assert ("Weather", renderer.water_transition_state.current_state) in rows


def test_tile_inspector_uses_hovered_tile_when_nothing_selected(monkeypatch):
    world = make_world(width=3, height=3)
    world.tiles[2][2] = Tile("forest")
    renderer = make_renderer(world)
    monkeypatch.setattr(renderer, "hovered_world_tile", lambda: (2, 2))
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_tile_inspector(0, 0, 200, 200)

    assert ("Tile", "(2, 2)") in rows
    assert ("Terrain", TERRAIN_LABELS["forest"]) in rows


def test_map_and_tile_inspector_use_same_visual_state_source():
    world = make_world(width=3, height=3)
    world.tiles[0][0] = Tile("wetland")
    world.season_index = 3
    renderer = make_renderer(world)

    renderer.draw_world()
    map_pixel = renderer.screen.get_at((1, 1))[:3]

    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=renderer.grass_transition_state,
        water_state=renderer.water_transition_state,
        base_moisture=renderer.tile_moisture(0, 0),
    )
    assert map_pixel in renderer.terrain_renderer.microtile_colors_for(context)
    assert ("Season", renderer.terrain_renderer.visual_state_for(context).season) in renderer.tile_inspector_rows(0, 0)


def test_renderer_uses_shared_terrain_renderer_for_visible_tiles(monkeypatch):
    world = make_world(width=4, height=2)
    world.tiles = [
        [Tile("grass"), Tile("water"), Tile("forest"), Tile("plain")],
        [Tile("hill"), Tile("path"), Tile("trampled_grass"), Tile("worn_grass")],
    ]
    renderer = make_renderer(world)
    rendered_kinds = []
    original_draw_tile = renderer.terrain_renderer.draw_tile

    def spy_draw_tile(surface, rect, context):
        rendered_kinds.append(context.tile.kind)
        original_draw_tile(surface, rect, context)

    monkeypatch.setattr(renderer.terrain_renderer, "draw_tile", spy_draw_tile)

    renderer.draw_world()

    assert rendered_kinds == [
        "grass",
        "water",
        "forest",
        "plain",
        "hill",
        "path",
        "trampled_grass",
        "worn_grass",
    ]


def test_terrain_pattern_generation_is_deterministic():
    world = make_world(width=1, height=1)
    world.seed = 123
    world.tiles[0][0] = Tile("hill")
    renderer = TerrainRenderer()
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
    )

    assert renderer.microtile_colors_for(context) == renderer.microtile_colors_for(context)
    assert len(renderer.microtile_colors_for(context)) == MICROTILE_RESOLUTION_BY_DETAIL[TERRAIN_RENDER_DETAIL] ** 2


def test_renderer_detail_levels_map_to_microtile_resolution():
    assert MICROTILE_RESOLUTION_BY_DETAIL[RENDER_DETAIL_LOW] == 1
    assert MICROTILE_RESOLUTION_BY_DETAIL[RENDER_DETAIL_MEDIUM] == 2
    assert MICROTILE_RESOLUTION_BY_DETAIL[RENDER_DETAIL_HIGH] == 3
    assert MICROTILE_RESOLUTION_BY_DETAIL[RENDER_DETAIL_ULTRA] == 5
    assert TERRAIN_RENDER_DETAIL == RENDER_DETAIL_HIGH


def test_microtile_grid_covers_tile_without_fixed_size_assumption():
    grid = MicrotileGrid(RENDER_DETAIL_HIGH)
    rects = grid.rects_for(pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE))

    assert len(rects) == 9
    assert rects[0].rect.topleft == (0, 0)
    assert rects[-1].rect.bottomright == (TILE_SIZE, TILE_SIZE)
    assert sum(rect.rect.width * rect.rect.height for rect in rects) == TILE_SIZE * TILE_SIZE


def test_pattern_generation_scales_with_render_detail_without_palette_changes():
    world = make_world(width=1, height=1)
    world.seed = 123
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
    )

    low = TerrainRenderer(detail_level=RENDER_DETAIL_LOW).microtile_pattern_for(context)
    high = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH).microtile_pattern_for(context)
    ultra = TerrainRenderer(detail_level=RENDER_DETAIL_ULTRA).microtile_pattern_for(context)

    assert low.resolution == 1
    assert high.resolution == 3
    assert ultra.resolution == 5
    assert len(low.colors) == 1
    assert len(high.colors) == 9
    assert len(ultra.colors) == 25


def test_pygame_renderer_defaults_to_high_detail():
    renderer = make_renderer(make_world(width=1, height=1))

    assert renderer.terrain_renderer.detail_level == RENDER_DETAIL_HIGH
    assert renderer.terrain_renderer.microtile_grid.resolution == 3


def test_map_cache_tracks_render_detail_changes():
    renderer = make_renderer(make_world(width=1, height=1))
    high_key = renderer.map_cache_state(0, 0, 1, 1)

    renderer.terrain_renderer.set_detail_level(RENDER_DETAIL_LOW)

    assert renderer.map_cache_state(0, 0, 1, 1) != high_key


def test_neighbourhood_analysis_reads_immediate_tiles_only():
    world = make_world(width=3, height=3)
    world.tiles[0][1] = Tile("forest")
    world.tiles[1][2] = Tile("water")
    world.tiles[2][0] = Tile(PATH)

    neighbourhood = TerrainNeighbourhood.from_world(world, 1, 1)

    assert neighbourhood.kind_at("n") == "forest"
    assert neighbourhood.kind_at("e") == "water"
    assert neighbourhood.kind_at("sw") == PATH
    assert neighbourhood.kind_at("nw") == "grass"
    assert TerrainNeighbourhood.from_world(world, 0, 0).kind_at("nw") is None


def test_terrain_transition_priorities_keep_water_dominant():
    assert TERRAIN_TRANSITION_PRIORITY["water"] > TERRAIN_TRANSITION_PRIORITY["forest"]
    assert TERRAIN_TRANSITION_PRIORITY["forest"] > TERRAIN_TRANSITION_PRIORITY["grass"]
    assert TERRAIN_TRANSITION_PRIORITY[PATH] > TERRAIN_TRANSITION_PRIORITY["grass"]


def test_forest_edge_shaping_preserves_forest_identity_deterministically():
    world = make_world(width=3, height=1)
    world.seed = 19
    world.tiles[0] = [Tile("grass"), Tile("forest"), Tile("grass")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    plain_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
    )
    edge_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        neighbourhood=TerrainNeighbourhood.from_world(world, 1, 0),
    )

    assert renderer.microtile_colors_for(edge_context) == renderer.microtile_colors_for(edge_context)
    plain = renderer.microtile_colors_for(plain_context)
    shaped = renderer.microtile_colors_for(edge_context)
    forest_state = renderer.visual_state_for(edge_context)
    forest_palette = set(TerrainPaletteManager().palette_for(forest_state))
    grass_palette = set(TerrainPaletteManager().palette_for_neighbour("grass", forest_state))

    assert shaped[4] == plain[4]
    assert shaped[4] in forest_palette
    assert set(shaped).issubset(set(plain) | forest_palette | grass_palette)


def test_water_and_path_edges_use_microtile_masks_without_changing_tile_kind():
    world = make_world(width=3, height=1)
    world.seed = 23
    world.tiles[0] = [Tile("water"), Tile("grass"), Tile(PATH)]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    grass_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 1, 0),
    )
    grass_without_edges = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )

    visual_state = renderer.visual_state_for(grass_context)
    shaped = renderer.microtile_colors_for(grass_context)
    unshaped = renderer.microtile_colors_for(grass_without_edges)
    manager = TerrainPaletteManager()
    allowed = set(unshaped)
    allowed.update(manager.palette_for_neighbour("water", visual_state))
    allowed.update(manager.palette_for_neighbour(PATH, visual_state))

    assert visual_state.terrain == "grass"
    assert shaped[4] == unshaped[4]
    assert set(shaped).issubset(allowed)
    assert world.tiles[0][1].kind == "grass"


def test_edge_masks_scale_with_ultra_microtile_resolution():
    world = make_world(width=2, height=1)
    world.seed = 31
    world.tiles[0] = [Tile("plain"), Tile("hill")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_ULTRA)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 0, 0),
    )
    pattern = renderer.microtile_pattern_for(context)

    assert pattern.resolution == 5
    assert len(pattern.colors) == 25


def test_renderer_context_includes_neighbourhood_for_visible_tiles():
    world = make_world(width=2, height=1)
    world.tiles[0] = [Tile("grass"), Tile("forest")]
    renderer = make_renderer(world)

    context = renderer.terrain_render_context(0, 0)

    assert context.neighbourhood is not None
    assert context.neighbourhood.kind_at("e") == "forest"


def test_renderer_art_config_loads_external_visual_settings():
    config = load_renderer_art_config(DEFAULT_RENDERER_CONFIG_PATH)

    assert config.source_path == DEFAULT_RENDERER_CONFIG_PATH
    assert config.master_vegetation_palettes["Spring"] == MASTER_VEGETATION_PALETTES["Spring"]
    assert config.path_palettes[PATH]["Normal"] == PATH_PALETTES[PATH][NORMAL]
    assert "dense_canopy" in config.terrain_motifs["forest"]
    assert not config.path_visual_language.edge_shaping_enabled
    assert config.sprite_pipeline.reserved_layers[0] == "terrain"


def test_master_vegetation_palette_harmonizes_grass_and_forest():
    world = make_world(width=2, height=1)
    manager = TerrainPaletteManager()
    grass_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )
    forest_tile = Tile("forest")
    forest_context = TerrainRenderContext(
        world=world,
        tile=forest_tile,
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
    )
    renderer = TerrainRenderer()
    grass_palette = manager.palette_for(renderer.visual_state_for(grass_context))
    forest_palette = manager.palette_for(renderer.visual_state_for(forest_context))
    master = MASTER_VEGETATION_PALETTES[world.season]

    assert palette_spread(grass_palette) < palette_spread(GRASS_MOISTURE_PALETTES[world.season][NORMAL])
    assert palette_spread(forest_palette) < palette_spread(FOREST_SEASON_PALETTES[world.season])
    assert min(_test_color_distance(color, master_color) for color in grass_palette for master_color in master) < 45
    assert min(_test_color_distance(color, master_color) for color in forest_palette for master_color in master) < 70


def test_spring_forests_remain_darker_than_surrounding_grass():
    world = make_world(width=2, height=1)
    renderer = TerrainRenderer()
    manager = TerrainPaletteManager()
    grass_state = renderer.visual_state_for(
        TerrainRenderContext(
            world=world,
            tile=Tile("grass"),
            tile_x=0,
            tile_y=0,
            grass_state=GrassMoistureTransitionState(),
            water_state=WaterTransitionState(),
            base_moisture=0.5,
        )
    )
    forest_state = renderer.visual_state_for(
        TerrainRenderContext(
            world=world,
            tile=Tile("forest"),
            tile_x=1,
            tile_y=0,
            grass_state=GrassMoistureTransitionState(),
            water_state=WaterTransitionState(),
        )
    )

    assert _test_brightness(_average_test_color(manager.palette_for(forest_state))) < _test_brightness(_average_test_color(manager.palette_for(grass_state)))


def test_autumn_keeps_more_colour_diversity_than_summer():
    world = make_world(width=1, height=1)
    renderer = TerrainRenderer()
    manager = TerrainPaletteManager()
    world.season_index = 1
    summer_state = renderer.visual_state_for(
        TerrainRenderContext(
            world=world,
            tile=Tile("grass"),
            tile_x=0,
            tile_y=0,
            grass_state=GrassMoistureTransitionState(),
            water_state=WaterTransitionState(),
            base_moisture=0.5,
        )
    )
    world.season_index = 2
    autumn_state = TerrainRenderContext(
        world=world,
        tile=Tile("grass"),
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )
    autumn_visual = renderer.visual_state_for(autumn_state)

    assert palette_spread(manager.palette_for(autumn_visual)) >= palette_spread(manager.palette_for(summer_state))


def test_motif_pattern_generation_clusters_microtiles():
    world = make_world(width=1, height=1)
    world.seed = 41
    world.tiles[0][0] = Tile("forest")
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_ULTRA)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
    )
    pattern = renderer.microtile_pattern_for(context)
    adjacent_matches = 0
    for row in range(pattern.resolution):
        for column in range(pattern.resolution - 1):
            if pattern.colors[row * pattern.resolution + column] == pattern.colors[row * pattern.resolution + column + 1]:
                adjacent_matches += 1

    assert adjacent_matches >= 6


def test_edge_shaping_uses_single_terrain_ownership_without_muddy_colours():
    world = make_world(width=3, height=1)
    world.seed = 53
    world.tiles[0] = [Tile("water"), Tile("grass"), Tile("hill")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 1, 0),
    )
    unshaped_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )
    shaped = renderer.microtile_colors_for(context)
    unshaped = renderer.microtile_colors_for(unshaped_context)
    visual_state = renderer.visual_state_for(context)
    manager = TerrainPaletteManager()
    allowed = set(unshaped)
    allowed.update(manager.palette_for_neighbour("water", visual_state))
    allowed.update(manager.palette_for_neighbour("hill", visual_state))

    assert shaped[4] == unshaped[4]
    assert set(shaped).issubset(allowed)


def test_path_edge_shaping_is_disabled_for_constructed_readability():
    world = make_world(width=2, height=1)
    world.seed = 83
    world.tiles[0] = [Tile(PATH), Tile("water")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    path_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 0, 0),
    )
    unshaped_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )

    assert renderer.microtile_colors_for(path_context) == renderer.microtile_colors_for(unshaped_context)


def test_forest_encroachment_adds_subtle_nature_to_adjacent_paths():
    world = make_world(width=2, height=1)
    world.seed = 2
    world.tiles[0] = [Tile(PATH), Tile("forest")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 0, 0),
    )
    state = renderer.visual_state_for(context)
    base = MicrotilePattern(3, tuple([(150, 112, 72)] * 9))
    encroached = PathForestEncroachment().apply(base, state, context)

    assert encroached.colors[4] == base.colors[4]
    assert any(color != base.colors[index] for index, color in enumerate(encroached.colors))
    assert all(_test_color_distance(color, base.colors[index]) < 50 for index, color in enumerate(encroached.colors))


def test_crop_palette_harmonizes_with_seasonal_vegetation():
    spring_palette = farm_stage_palette("Growing", "Spring")
    raw_palette = FARM_STAGE_PALETTES["Growing"]
    master = MASTER_VEGETATION_PALETTES["Spring"]

    assert palette_spread(spring_palette) <= palette_spread(raw_palette)
    assert min(_test_color_distance(color, master_color) for color in spring_palette for master_color in master) < 45


def test_forest_ambient_occlusion_subtly_darkens_neighbouring_grass():
    world = make_world(width=2, height=1)
    world.seed = 67
    world.tiles[0] = [Tile("grass"), Tile("forest")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 0, 0),
    )
    state = renderer.visual_state_for(context)
    base = MicrotilePattern(3, tuple([(100, 150, 90)] * 9))
    shaded = AmbientTerrainOcclusion().apply(base, state, context)

    assert shaded.colors[4] == base.colors[4]
    assert any(_test_brightness(color) < _test_brightness(base.colors[index]) for index, color in enumerate(shaded.colors))
    assert all(_test_brightness(color) >= int(_test_brightness(base.colors[index]) * 0.88) for index, color in enumerate(shaded.colors))


def test_forest_ambient_occlusion_does_not_affect_water_paths_or_farms():
    world = make_world(width=3, height=1)
    world.seed = 71
    world.tiles[0] = [Tile("water"), Tile(PATH), Tile("forest")]
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_HIGH)
    occlusion = AmbientTerrainOcclusion()
    base = MicrotilePattern(3, tuple([(100, 150, 90)] * 9))

    for x in (0, 1):
        context = TerrainRenderContext(
            world=world,
            tile=world.tiles[0][x],
            tile_x=x,
            tile_y=0,
            grass_state=GrassMoistureTransitionState(),
            water_state=WaterTransitionState(),
            base_moisture=0.5,
            neighbourhood=TerrainNeighbourhood.from_world(world, x, 0),
        )
        assert occlusion.apply(base, renderer.visual_state_for(context), context) == base

    farm_world = make_world(width=2, height=1)
    farm_world.tiles[0] = [Tile("grass"), Tile("forest")]
    farm_world.settlement = Settlement("Farm Test", 0, 0, 1, "Spring")
    farm_world.settlement.farm_plots.append(FarmPlot(0, 0, tuple(((0, 0), (0, 1), (1, 0), (1, 1)))))
    farm_context = TerrainRenderContext(
        world=farm_world,
        tile=farm_world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        gameplay_state=GameplayVisualState(crop_state=FIELD_GROWING),
        neighbourhood=TerrainNeighbourhood.from_world(farm_world, 0, 0),
    )
    assert occlusion.apply(base, renderer.visual_state_for(farm_context), farm_context) == base


def test_dense_forest_ambient_occlusion_can_reach_second_microtile_at_ultra_detail():
    world = make_world(width=3, height=3)
    world.seed = 73
    for x, y in ((0, 1), (1, 0), (2, 1), (1, 2)):
        world.tiles[y][x] = Tile("forest")
    renderer = TerrainRenderer(detail_level=RENDER_DETAIL_ULTRA)
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[1][1],
        tile_x=1,
        tile_y=1,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        neighbourhood=TerrainNeighbourhood.from_world(world, 1, 1),
    )
    state = renderer.visual_state_for(context)
    base = MicrotilePattern(5, tuple([(100, 150, 90)] * 25))
    shaded = AmbientTerrainOcclusion().apply(base, state, context)
    second_ring_indices = (6, 7, 8, 11, 13, 16, 17, 18)

    assert any(shaded.colors[index] != base.colors[index] for index in second_ring_indices)
    assert shaded.colors[12] == base.colors[12]


def test_plains_and_hills_keep_base_moisture_when_weather_is_overlay():
    world = make_world(width=2, height=1)
    world.tiles[0][0] = Tile("plain")
    world.tiles[0][1] = Tile("hill")
    renderer = TerrainRenderer()
    wet_state = GrassMoistureTransitionState(previous_mode=GRASS_HEAVY_RAIN, current_mode=GRASS_HEAVY_RAIN)

    plain_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=wet_state,
        water_state=WaterTransitionState(),
        base_moisture=0.2,
    )
    hill_context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][1],
        tile_x=1,
        tile_y=0,
        grass_state=wet_state,
        water_state=WaterTransitionState(),
        base_moisture=0.2,
    )

    assert renderer.visual_state_for(plain_context).moisture_state == DRY
    assert renderer.visual_state_for(hill_context).moisture_state == DRY
    assert renderer.microtile_colors_for(plain_context) != renderer.microtile_colors_for(hill_context)


def test_path_and_trampled_ground_keep_base_moisture_when_weather_is_overlay():
    world = make_world(width=4, height=1)
    world.tiles[0] = [Tile(TRAMPLED_GRASS), Tile(WORN_GRASS), Tile(DIRT_PATH), Tile(PATH)]
    renderer = TerrainRenderer()
    wet_state = GrassMoistureTransitionState(previous_mode=GRASS_HEAVY_RAIN, current_mode=GRASS_HEAVY_RAIN)

    for x, tile in enumerate(world.tiles[0]):
        context = TerrainRenderContext(
            world=world,
            tile=tile,
            tile_x=x,
            tile_y=0,
            grass_state=wet_state,
            water_state=WaterTransitionState(),
            base_moisture=0.2,
        )

        assert renderer.visual_state_for(context).moisture_state == DRY
        assert renderer.microtile_colors_for(context) == renderer.microtile_colors_for(context)
        assert palette_spread(renderer.microtile_colors_for(context)) <= palette_spread(PATH_PALETTES[tile.kind][DRY])


def test_grassland_seasonal_transition_uses_distributed_visual_season_after_start():
    world = make_world(width=4, height=4)
    world.seed = 44
    world.day = 21
    world.season_index = 1
    renderer = TerrainRenderer()
    visual_seasons = set()

    for y in range(4):
        for x in range(4):
            world.tiles[y][x] = Tile("plain")
            context = TerrainRenderContext(
                world=world,
                tile=world.tiles[y][x],
                tile_x=x,
                tile_y=y,
                grass_state=GrassMoistureTransitionState(),
                water_state=WaterTransitionState(),
                base_moisture=0.5,
            )
            visual_seasons.add(renderer.visual_state_for(context).visual_season)

    assert visual_seasons.issubset({"Spring", "Summer"})
    assert len(visual_seasons) > 1


def test_crop_visual_stage_maps_current_and_future_farm_states():
    assert crop_visual_stage(FIELD_UNPREPARED) == "Harvested"
    assert crop_visual_stage(FIELD_PLANTED, growth=0) == "Planted"
    assert crop_visual_stage(FIELD_PLANTED, growth=4) == "Sprouting"
    assert crop_visual_stage(FIELD_GROWING) == "Growing"
    assert crop_visual_stage(FIELD_READY) == "Mature"
    assert crop_visual_stage(FIELD_DORMANT) == "Fallow"
    assert crop_visual_stage("Prepared") == "Prepared"


def test_farm_gameplay_state_modifies_final_palette_without_changing_tile_kind():
    world = make_world(width=1, height=1)
    tile = world.tiles[0][0]
    renderer = TerrainRenderer()
    base_context = TerrainRenderContext(
        world=world,
        tile=tile,
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
    )
    farm_context = TerrainRenderContext(
        world=world,
        tile=tile,
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        gameplay_state=GameplayVisualState(crop_state=FIELD_READY, crop_growth=100, crop_food=4),
    )

    assert renderer.microtile_colors_for(farm_context) != renderer.microtile_colors_for(base_context)
    assert renderer.visual_state_for(farm_context).terrain == "grass"
    assert set(renderer.microtile_colors_for(farm_context)).isdisjoint(FARM_STAGE_PALETTES["Empty"])


def test_construction_progress_uses_renderer_only_visual_stage():
    assert construction_visual_stage(1, 15) == "Foundation"
    assert construction_visual_stage(8, 15) == "Under Construction"
    assert construction_visual_stage(15, 15) == "Completed"

    world = make_world(width=1, height=1)
    renderer = TerrainRenderer()
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        gameplay_state=GameplayVisualState(construction_progress=1, construction_max=15),
    )

    assert renderer.microtile_colors_for(context)
    assert renderer.microtile_colors_for(context) != FARM_STAGE_PALETTES["Empty"]
    assert CONSTRUCTION_PALETTES["Foundation"]


def test_future_visual_modifiers_are_composable_and_deterministic():
    world = make_world(width=1, height=1)
    renderer = TerrainRenderer()
    gameplay = GameplayVisualState(
        modifiers=(
            TerrainVisualModifier("snow", "Light Snow", 0.5),
            TerrainVisualModifier("magic", "Mystical", 0.4),
        )
    )
    context = TerrainRenderContext(
        world=world,
        tile=world.tiles[0][0],
        tile_x=0,
        tile_y=0,
        grass_state=GrassMoistureTransitionState(),
        water_state=WaterTransitionState(),
        base_moisture=0.5,
        gameplay_state=gameplay,
    )

    assert renderer.microtile_colors_for(context) == renderer.microtile_colors_for(context)
    assert renderer.microtile_colors_for(context) != TerrainRenderer().microtile_colors_for(
        TerrainRenderContext(
            world=world,
            tile=world.tiles[0][0],
            tile_x=0,
            tile_y=0,
            grass_state=GrassMoistureTransitionState(),
            water_state=WaterTransitionState(),
            base_moisture=0.5,
        )
    )


def test_pygame_renderer_exposes_farm_and_construction_gameplay_state():
    world = make_world(width=4, height=4)
    world.settlement = Settlement("Test", 1, 1, 1, "Spring")
    farm = FarmPlot(1, 1)
    farm.crop_state = FIELD_READY
    farm.growth = 100
    farm.food = 4
    world.settlement.farm_plots.append(farm)
    world.settlement.construction_progress[(3, 3)] = 4
    renderer = make_renderer(world)

    farm_state = renderer.terrain_gameplay_state(1, 1)
    construction_state = renderer.terrain_gameplay_state(3, 3)

    assert farm_state is not None
    assert farm_state.crop_state == FIELD_READY
    assert construction_state is not None
    assert construction_state.construction_progress == 4


def test_tile_color_helper_still_uses_blended_transition_color():
    world = make_world(width=3, height=3)
    world.day = 20
    world.tick = TICKS_PER_DAY // 2
    renderer = make_renderer(world)

    color = renderer.tile_color("plain")
    assert color != seasonal_tile_color("plain", "Spring")
    assert color != seasonal_tile_color("plain", "Summer")


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
    assert terrain_pixel in renderer.terrain_renderer.microtile_colors_for(renderer.terrain_render_context(1, 1))


def test_forest_terrain_remains_visible_when_wood_resource_is_unknown():
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.tiles[1][1].wood = 2
    renderer = make_renderer(world)

    renderer.draw_world()

    terrain_pixel = renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + 1))[:3]
    context = renderer.terrain_render_context(1, 1)
    assert renderer.terrain_renderer.visual_state_for(context).terrain == "forest"
    assert terrain_pixel in renderer.terrain_renderer.microtile_colors_for(context)


def test_forest_tile_draws_deterministic_subcell_canopy():
    world = make_world(width=3, height=3)
    world.seed = 99
    world.tiles[1][1].kind = "forest"
    renderer = make_renderer(world)

    renderer.draw_world()
    first_pixels = [
        renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + TILE_SIZE - 2, 1 * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + TILE_SIZE - 2))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + TILE_SIZE - 2, 1 * TILE_SIZE + TILE_SIZE - 2))[:3],
    ]
    renderer.invalidate_map_cache()
    renderer.draw_world()
    second_pixels = [
        renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + TILE_SIZE - 2, 1 * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + 1, 1 * TILE_SIZE + TILE_SIZE - 2))[:3],
        renderer.screen.get_at((1 * TILE_SIZE + TILE_SIZE - 2, 1 * TILE_SIZE + TILE_SIZE - 2))[:3],
    ]

    assert first_pixels == second_pixels
    assert len(set(first_pixels)) > 1


def test_forest_subcell_palette_changes_by_season():
    spring = forest_subcell_colors(7, 1, 1, "Spring", FOREST_SEASON_TRANSITION_DAYS + 1)
    autumn = forest_subcell_colors(7, 1, 1, "Autumn", FOREST_SEASON_TRANSITION_DAYS + 1)
    winter = forest_subcell_colors(7, 1, 1, "Winter", FOREST_SEASON_TRANSITION_DAYS + 1)

    assert spring != autumn
    assert autumn != winter
    assert all(color in FOREST_SEASON_PALETTES["Spring"] for color in spring)
    assert all(color in FOREST_SEASON_PALETTES["Autumn"] for color in autumn)
    assert all(color in FOREST_SEASON_PALETTES["Winter"] for color in winter)


def test_summer_forest_trunks_are_rare_in_deterministic_palette():
    trunk = (104, 70, 42)
    samples = [
        color
        for x in range(20)
        for y in range(20)
        for color in forest_subcell_colors(11, x, y, "Summer", FOREST_SEASON_TRANSITION_DAYS + 1)
    ]

    assert samples.count(trunk) / len(samples) < 0.05


def test_forest_appearance_is_stable_throughout_same_season_day():
    colors = [
        forest_subcell_colors(21, 1, 1, "Spring", day)
        for day in range(FOREST_SEASON_TRANSITION_DAYS + 1, FOREST_SEASON_TRANSITION_DAYS + 8)
    ]

    assert len(set(colors)) == 1


def test_forest_transition_day_is_deterministic_and_spread_across_window():
    days = {
        forest_transition_day(31, x, y, "Autumn")
        for x in range(8)
        for y in range(8)
    }

    assert min(days) >= 1
    assert max(days) <= FOREST_SEASON_TRANSITION_DAYS
    assert len(days) > 1


def test_forest_visual_season_waits_until_tile_transition_day():
    seed = 41
    tile_x = 3
    tile_y = 5
    season = "Autumn"
    transition_day = forest_transition_day(seed, tile_x, tile_y, season)

    if transition_day > 1:
        assert forest_visual_season(seed, tile_x, tile_y, season, transition_day - 1) == "Summer"
    assert forest_visual_season(seed, tile_x, tile_y, season, transition_day) == season


def test_forest_transition_cache_changes_only_during_transition_days():
    world = make_world(width=3, height=3)
    world.seed = 14
    world.tiles[1][1].kind = "forest"
    renderer = make_renderer(world)
    viewport_rebuilds = []
    original_viewport_rebuild = renderer.rebuild_map_surface
    chunk_rebuilds = []
    original_chunk_rebuild = renderer.rebuild_chunk

    def spy_viewport_rebuild(start_x, start_y, end_x, end_y):
        viewport_rebuilds.append((world.day_of_season, world.tick))
        original_viewport_rebuild(start_x, start_y, end_x, end_y)

    def spy_chunk_rebuild(chunk):
        chunk_rebuilds.append((world.day_of_season, world.tick, chunk.chunk_x, chunk.chunk_y))
        original_chunk_rebuild(chunk)

    renderer.rebuild_map_surface = spy_viewport_rebuild
    renderer.rebuild_chunk = spy_chunk_rebuild

    renderer.draw_world()
    partials = []
    world.tick += 1
    renderer.draw_world()
    partials.append(renderer.last_partial_redraw_count)
    world.day += 1
    renderer.draw_world()
    partials.append(renderer.last_partial_redraw_count)
    world.day += FOREST_SEASON_TRANSITION_DAYS + 2
    renderer.draw_world()
    partials.append(renderer.last_partial_redraw_count)
    world.day += 1
    renderer.draw_world()
    partials.append(renderer.last_partial_redraw_count)

    assert viewport_rebuilds == []
    assert chunk_rebuilds[0] == (1, 0, 0, 0)
    assert any(count > 0 for count in partials)
    assert renderer.renderer_revisions["season"] > 0


def grass_tile_pixels(renderer, tile_x: int = 1, tile_y: int = 1):
    return [
        renderer.screen.get_at((tile_x * TILE_SIZE + 1, tile_y * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + TILE_SIZE - 2, tile_y * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + 1, tile_y * TILE_SIZE + TILE_SIZE - 2))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + TILE_SIZE - 2, tile_y * TILE_SIZE + TILE_SIZE - 2))[:3],
    ]


def test_grass_tile_draws_deterministic_subcell_surface():
    world = make_world(width=3, height=3)
    world.seed = 99
    world.tiles[1][1].kind = "grass"
    world.moisture_map = [[0.5 for _ in range(3)] for _ in range(3)]
    renderer = make_renderer(world)

    renderer.draw_world()
    first_pixels = grass_tile_pixels(renderer)
    renderer.invalidate_map_cache()
    renderer.draw_world()
    second_pixels = grass_tile_pixels(renderer)

    assert first_pixels == second_pixels
    assert len(set(first_pixels)) > 1
    context = renderer.terrain_render_context(1, 1)
    assert all(color in renderer.terrain_renderer.microtile_colors_for(context) for color in first_pixels)


def test_grass_moisture_palette_changes_by_state_and_season():
    dry_summer = grass_subcell_colors(7, 1, 1, "Summer", 0.2, GrassMoistureTransitionState(), world_tick=0)
    wet_summer = grass_subcell_colors(
        7,
        1,
        1,
        "Summer",
        0.2,
        GrassMoistureTransitionState(previous_mode=GRASS_HEAVY_RAIN, current_mode=GRASS_HEAVY_RAIN),
        world_tick=0,
    )
    wet_winter = grass_subcell_colors(
        7,
        1,
        1,
        "Winter",
        0.2,
        GrassMoistureTransitionState(previous_mode=GRASS_HEAVY_RAIN, current_mode=GRASS_HEAVY_RAIN),
        world_tick=0,
    )

    assert dry_summer != wet_summer
    assert wet_summer != wet_winter
    assert all(color in GRASS_MOISTURE_PALETTES["Summer"][DRY] for color in dry_summer)
    assert all(color in GRASS_MOISTURE_PALETTES["Summer"][WET] for color in wet_summer)
    assert all(color in GRASS_MOISTURE_PALETTES["Winter"][WET] for color in wet_winter)


def test_grass_moisture_state_uses_base_moisture_when_clear():
    assert grass_moisture_state(0.2, "clear") == DRY
    assert grass_moisture_state(0.5, "clear") == NORMAL
    assert grass_moisture_state(0.8, "clear") == WET
    assert grass_moisture_state(0.2, GRASS_HEAVY_RAIN) == WET


def test_grass_transition_tick_is_deterministic_and_spread_across_window():
    ticks = {
        grass_transition_tick(31, x, y, GRASS_HEAVY_RAIN, transition_id=1)
        for x in range(8)
        for y in range(8)
    }

    assert min(ticks) >= 0
    assert max(ticks) <= GRASS_MOISTURE_TRANSITION_HOURS * TICKS_PER_HOUR
    assert len(ticks) > 1


def test_grass_visual_moisture_mode_waits_until_tile_transition_tick():
    state = GrassMoistureTransitionState(
        previous_mode="clear",
        current_mode=GRASS_HEAVY_RAIN,
        transition_start_tick=100,
        transition_id=2,
    )
    tile_x = 3
    tile_y = 5
    transition_tick = grass_transition_tick(41, tile_x, tile_y, GRASS_HEAVY_RAIN, transition_id=2)

    if transition_tick > 0:
        assert grass_visual_moisture_mode(41, tile_x, tile_y, state, 100 + transition_tick - 1) == "clear"
    assert grass_visual_moisture_mode(41, tile_x, tile_y, state, 100 + transition_tick) == GRASS_HEAVY_RAIN


def test_grass_moisture_weather_overlay_does_not_dirty_terrain_cache():
    world = make_world(width=3, height=3)
    world.seed = 14
    world.tiles[1][1].kind = "grass"
    renderer = make_renderer(world)
    viewport_rebuilds = []
    original_viewport_rebuild = renderer.rebuild_map_surface
    chunk_rebuilds = []
    original_chunk_rebuild = renderer.rebuild_chunk

    def spy_viewport_rebuild(start_x, start_y, end_x, end_y):
        viewport_rebuilds.append((renderer.grass_transition_state.current_mode, world.tick))
        original_viewport_rebuild(start_x, start_y, end_x, end_y)

    def spy_chunk_rebuild(chunk):
        chunk_rebuilds.append((renderer.grass_transition_state.current_mode, world.tick, chunk.chunk_x, chunk.chunk_y))
        original_chunk_rebuild(chunk)

    renderer.rebuild_map_surface = spy_viewport_rebuild
    renderer.rebuild_chunk = spy_chunk_rebuild

    renderer.draw_world()
    world.tick += 1
    renderer.draw_world()
    before_event_redraws = renderer.last_partial_redraw_count
    world.active_environment_events.append(create_environment_event("heavy_rain", duration_days=2))
    overlay_state = renderer.environmental_overlay_state()
    renderer.draw_world()
    event_redraws = renderer.last_partial_redraw_count
    world.tick += 1
    renderer.draw_world()
    transition_redraws = renderer.last_partial_redraw_count

    assert viewport_rebuilds == []
    assert chunk_rebuilds[0] == ("clear", 0, 0, 0)
    assert len(chunk_rebuilds) == 1
    assert before_event_redraws == 0
    assert event_redraws == 0
    assert transition_redraws == 0
    assert renderer.renderer_revisions["moisture"] == 0
    assert renderer.environmental_overlay_state() != overlay_state


def water_tile_pixels(renderer, tile_x: int = 1, tile_y: int = 1):
    return [
        renderer.screen.get_at((tile_x * TILE_SIZE + 1, tile_y * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + TILE_SIZE - 2, tile_y * TILE_SIZE + 1))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + 1, tile_y * TILE_SIZE + TILE_SIZE - 2))[:3],
        renderer.screen.get_at((tile_x * TILE_SIZE + TILE_SIZE - 2, tile_y * TILE_SIZE + TILE_SIZE - 2))[:3],
    ]


def test_water_tile_draws_deterministic_subcell_surface():
    world = make_world(width=3, height=3)
    world.seed = 99
    world.tiles[1][1].kind = "water"
    renderer = make_renderer(world)

    renderer.draw_world()
    first_pixels = water_tile_pixels(renderer)
    renderer.invalidate_map_cache()
    renderer.draw_world()
    second_pixels = water_tile_pixels(renderer)

    assert first_pixels == second_pixels
    assert len(set(first_pixels)) > 1
    context = renderer.terrain_render_context(1, 1)
    assert renderer.terrain_renderer.visual_state_for(context).weather_state == CLEAR
    assert all(color in renderer.terrain_renderer.microtile_colors_for(context) for color in first_pixels)


def test_water_weather_palette_changes_by_weather_state():
    clear = water_subcell_colors(7, 1, 1, WaterTransitionState(current_state=CLEAR), world_tick=0)
    rain = water_subcell_colors(7, 1, 1, WaterTransitionState(previous_state=RAIN, current_state=RAIN), world_tick=0)
    heavy = water_subcell_colors(7, 1, 1, WaterTransitionState(previous_state=HEAVY_RAIN, current_state=HEAVY_RAIN), world_tick=0)

    assert clear != rain
    assert rain != heavy
    assert all(color in WATER_WEATHER_PALETTES[CLEAR] for color in clear)
    assert all(color in WATER_WEATHER_PALETTES[RAIN] for color in rain)
    assert all(color in WATER_WEATHER_PALETTES[HEAVY_RAIN] for color in heavy)


def test_weather_state_detects_heavy_rain_event():
    assert weather_state_for_events([]) == CLEAR
    assert weather_state_for_events([create_environment_event("heavy_rain", duration_days=2)]) == HEAVY_RAIN


def test_water_transition_tick_is_deterministic_and_spread_across_window():
    state = HEAVY_RAIN
    ticks = {
        water_transition_tick(31, x, y, state, transition_id=1)
        for x in range(8)
        for y in range(8)
    }

    assert min(ticks) >= 0
    assert max(ticks) <= WATER_WEATHER_TRANSITION_HOURS * TICKS_PER_HOUR
    assert len(ticks) > 1


def test_water_visual_weather_waits_until_tile_transition_tick():
    state = WaterTransitionState(previous_state=CLEAR, current_state=HEAVY_RAIN, transition_start_tick=100, transition_id=2)
    tile_x = 3
    tile_y = 5
    transition_tick = water_transition_tick(41, tile_x, tile_y, HEAVY_RAIN, transition_id=2)

    if transition_tick > 0:
        assert water_visual_weather(41, tile_x, tile_y, state, 100 + transition_tick - 1) == CLEAR
    assert water_visual_weather(41, tile_x, tile_y, state, 100 + transition_tick) == HEAVY_RAIN


def test_water_weather_overlay_does_not_dirty_terrain_cache():
    world = make_world(width=3, height=3)
    world.seed = 14
    world.tiles[1][1].kind = "water"
    renderer = make_renderer(world)
    viewport_rebuilds = []
    original_viewport_rebuild = renderer.rebuild_map_surface
    chunk_rebuilds = []
    original_chunk_rebuild = renderer.rebuild_chunk

    def spy_viewport_rebuild(start_x, start_y, end_x, end_y):
        viewport_rebuilds.append((renderer.water_transition_state.current_state, world.tick))
        original_viewport_rebuild(start_x, start_y, end_x, end_y)

    def spy_chunk_rebuild(chunk):
        chunk_rebuilds.append((renderer.water_transition_state.current_state, world.tick, chunk.chunk_x, chunk.chunk_y))
        original_chunk_rebuild(chunk)

    renderer.rebuild_map_surface = spy_viewport_rebuild
    renderer.rebuild_chunk = spy_chunk_rebuild

    renderer.draw_world()
    world.tick += 1
    renderer.draw_world()
    before_event_redraws = renderer.last_partial_redraw_count
    world.active_environment_events.append(create_environment_event("heavy_rain", duration_days=2))
    overlay_state = renderer.environmental_overlay_state()
    renderer.draw_world()
    event_redraws = renderer.last_partial_redraw_count
    transition_redraws = []
    for _ in range(40):
        world.tick += 1
        renderer.draw_world()
        transition_redraws.append(renderer.last_partial_redraw_count)

    assert viewport_rebuilds == []
    assert chunk_rebuilds[0] == (CLEAR, 0, 0, 0)
    assert len(chunk_rebuilds) == 1
    assert before_event_redraws == 0
    assert event_redraws == 0
    assert sum(transition_redraws) == 0
    assert renderer.renderer_revisions["weather"] == 0
    assert renderer.environmental_overlay_state() != overlay_state


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

    def spy_draw_agent_symbol(agent, x, y, offset=(0, 0)):
        calls.append((agent, x, y, offset))

    monkeypatch.setattr(renderer, "draw_agent_symbol", spy_draw_agent_symbol)

    renderer.draw_world()

    drawn_agent, x, y, offset = calls[0]
    assert drawn_agent.agent_id == agent.agent_id or drawn_agent.name == agent.name
    assert drawn_agent.role == BUILDER
    assert (x, y, offset) == (1, 1, VILLAGER_TILE_OFFSETS[0])
    assert color_for_role(BUILDER)


def test_renderer_offsets_agents_that_share_a_tile(monkeypatch):
    world = make_world(width=3, height=3)
    agents = [
        Agent("Ari", 1, 1, agent_id="a"),
        Agent("Bryn", 1, 1, agent_id="b"),
        Agent("Cato", 1, 1, agent_id="c"),
    ]
    world.agents.extend(agents)
    renderer = make_renderer(world)
    calls = []

    def spy_draw_agent_symbol(agent, x, y, offset=(0, 0)):
        calls.append((agent.agent_id, x, y, offset))

    monkeypatch.setattr(renderer, "draw_agent_symbol", spy_draw_agent_symbol)

    renderer.draw_world()

    assert calls == [
        ("a", 1, 1, VILLAGER_TILE_OFFSETS[0]),
        ("b", 1, 1, VILLAGER_TILE_OFFSETS[1]),
        ("c", 1, 1, VILLAGER_TILE_OFFSETS[2]),
    ]


def test_renderer_draws_agents_through_observer_camera_transform(monkeypatch):
    world = make_world(width=100, height=80)
    agent = Agent("Ari", 3, 2)
    world.agents.append(agent)
    renderer = make_renderer(world)
    renderer.observer_camera.set_position(1, 1, snap=True)
    calls = []

    def spy_draw_agent_symbol(agent, x, y, offset=(0, 0)):
        calls.append((x, y, offset))

    monkeypatch.setattr(renderer, "draw_agent_symbol", spy_draw_agent_symbol)

    renderer.draw_world()

    assert calls == [(2.0, 1.0, VILLAGER_TILE_OFFSETS[0])]


def test_renderer_advances_agent_interpolation_without_world_update():
    world = make_world(width=3, height=3)
    agent = Agent("Ari", 0, 0)
    world.agents.append(agent)
    renderer = make_renderer(world)
    agent.x = 1

    renderer.update_agent_render_motion(0.05)

    snapshot = renderer.presentation_scene.last_snapshot.agents[0]
    render_x, render_y = snapshot.render_x, snapshot.render_y
    assert 0 < render_x < 1
    assert render_y == 0
    assert renderer.presentation_engine is renderer.presentation_scene


def test_renderer_advances_agent_across_multiple_path_nodes_without_logic_update():
    world = make_world(width=4, height=3)
    agent = Agent("Ari", 0, 1)
    world.agents.append(agent)
    renderer = make_renderer(world)
    agent.x = 3

    renderer.update_agent_render_motion(0.15)

    snapshot = renderer.presentation_scene.last_snapshot.agents[0]
    render_x, render_y = snapshot.render_x, snapshot.render_y
    assert 1 < render_x < 3
    assert render_y == 1


def test_renderer_update_ui_passes_pause_to_presentation_time():
    world = make_world(width=3, height=3)
    agent = Agent("Ari", 0, 0)
    world.agents.append(agent)
    renderer = make_renderer(world)
    agent.x = 1

    renderer.update_ui(0.25, paused=True)

    assert renderer.presentation_scene.presentation_time.paused
    assert renderer.presentation_scene.presentation_time.elapsed_seconds == 0
    assert renderer.presentation_scene.last_snapshot.agents[0].render_x == 0


def test_renderer_consumes_presentation_scene_for_agents(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Ari", 1, 1, agent_id="ari")
    world.agents.append(agent)
    renderer = make_renderer(world)
    consumed = []

    original_snapshot_world = renderer.presentation_scene.snapshot_world

    def spy_snapshot_world(world_arg):
        snapshot = original_snapshot_world(world_arg)
        consumed.append(snapshot)
        return snapshot

    monkeypatch.setattr(renderer.presentation_scene, "snapshot_world", spy_snapshot_world)

    renderer.draw_world()

    assert consumed
    assert consumed[0].agents[0].agent_id == "ari"


def test_renderer_receives_presentation_action_state(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Ari", 1, 1, agent_id="ari", current_action="Eating")
    world.agents.append(agent)
    renderer = make_renderer(world)
    consumed = []

    def spy_draw_agent_symbol(agent, x, y, offset=(0, 0)):
        consumed.append(agent)

    monkeypatch.setattr(renderer, "draw_agent_symbol", spy_draw_agent_symbol)

    renderer.update_agent_render_motion(0.20)
    renderer.draw_world()

    assert consumed[0].presentation_action == "Eating"
    assert consumed[0].presentation_action_state == "Performing"


def test_renderer_reuses_cached_map_surface_between_world_ticks(monkeypatch):
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)
    rebuilds = []
    original_rebuild = renderer.rebuild_chunk

    def spy_rebuild(chunk):
        rebuilds.append((chunk.chunk_x, chunk.chunk_y))
        original_rebuild(chunk)

    monkeypatch.setattr(renderer, "rebuild_chunk", spy_rebuild)

    renderer.draw_world()
    renderer.draw_world()

    assert len(rebuilds) == 1


def test_renderer_keeps_cached_map_surface_within_same_visual_tick_bucket(monkeypatch):
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)
    rebuilds = []
    original_rebuild = renderer.rebuild_chunk

    def spy_rebuild(chunk):
        rebuilds.append(world.tick)
        original_rebuild(chunk)

    monkeypatch.setattr(renderer, "rebuild_chunk", spy_rebuild)

    renderer.draw_world()
    world.tick += 1
    renderer.draw_world()

    assert rebuilds == [0]


def test_renderer_uses_ordered_scene_layers():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    assert [layer.name for layer in renderer.render_layers] == [
        "Terrain",
        "Vegetation",
        "Structures",
        "Environment",
        "Agents",
        "Effects",
        "UI",
    ]
    assert renderer.render_layers[0].cached is True
    assert renderer.render_layers[1].cached is False
    assert renderer.render_layers[3].cached is False
    assert renderer.diagnostics_metrics()["render_layers"] == tuple(layer.name for layer in renderer.render_layers)


def test_agent_and_ui_layers_do_not_dirty_terrain_chunks():
    world = make_world(width=3, height=3)
    agent = Agent("Eli", 1, 1, role=SCOUT)
    world.agents.append(agent)
    renderer = make_renderer(world)

    renderer.draw(False, 10, last_sim_ms=0, sim_ticks=0)
    assert renderer.last_chunk_rebuild_count > 0

    agent.x = 2
    agent.y = 1
    renderer.draw(False, 10, last_sim_ms=0, sim_ticks=0)

    assert renderer.last_chunk_rebuild_count == 0
    assert renderer.last_chunk_redraw_count == 0
    assert len(renderer.dirty_chunks) == 0


def test_season_visual_cache_state_is_stable_within_day():
    world = make_world(width=3, height=3)
    world.day = DAYS_PER_SEASON - 2
    world.tick = 0
    renderer = make_renderer(world)

    start_key = renderer.visual_transition_cache_state()
    world.tick = TICKS_PER_DAY // 2

    assert renderer.visual_transition_cache_state() == start_key


def test_weather_overlay_state_can_change_within_day_without_terrain_key_change():
    from src.environment_events import create_environment_event

    world = make_world(width=3, height=3)
    world.day = DAYS_PER_SEASON - 2
    world.tick = 10
    renderer = make_renderer(world)

    start_key = renderer.visual_transition_cache_state()
    start_overlay = renderer.environmental_overlay_state()
    world.active_environment_events.append(create_environment_event("heavy_rain", duration_days=2))
    weather_key = renderer.visual_transition_cache_state()

    assert weather_key == start_key
    assert renderer.environmental_overlay_state() != start_overlay


def test_tree_foliage_color_interpolates_smoothly_without_terrain_key_change():
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    world.day = DAYS_PER_SEASON // 2
    world.tick = 0
    renderer = make_renderer(world)

    start_key = renderer.visual_transition_cache_state()
    start_color = renderer.smooth_foliage_color()
    world.tick = TICKS_PER_DAY - 1

    assert renderer.visual_transition_cache_state() == start_key
    assert renderer.smooth_foliage_color() != start_color


def test_tree_foliage_motion_does_not_rebuild_terrain_chunks():
    world = make_world(width=3, height=3)
    world.tiles[1][1].kind = "forest"
    renderer = make_renderer(world)

    renderer.draw_world()
    assert renderer.last_chunk_rebuild_count > 0

    world.tick = TICKS_PER_DAY - 1
    renderer.draw_world()

    assert renderer.last_chunk_rebuild_count == 0
    assert renderer.last_chunk_redraw_count == 0
    assert len(renderer.dirty_chunks) == 0


def test_cloud_shadow_motion_does_not_dirty_terrain_chunks():
    world = make_world(width=3, height=3)
    world.active_environment_events.append(create_environment_event("heavy_rain", duration_days=2))
    renderer = make_renderer(world)

    renderer.draw_world()
    assert renderer.last_chunk_rebuild_count > 0
    start_overlay = renderer.environmental_overlay_state()

    world.tick += 18
    renderer.draw_world()

    assert renderer.environmental_overlay_state() != start_overlay
    assert renderer.last_chunk_rebuild_count == 0
    assert renderer.last_chunk_redraw_count == 0
    assert len(renderer.dirty_chunks) == 0


def test_camera_movement_reuses_cached_chunks(monkeypatch):
    world = make_world(width=96, height=45)
    renderer = make_renderer(world)

    renderer.draw_world()

    rebuilds = []
    original_rebuild = renderer.rebuild_chunk

    def spy_rebuild(chunk):
        rebuilds.append((chunk.chunk_x, chunk.chunk_y))
        original_rebuild(chunk)

    monkeypatch.setattr(renderer, "rebuild_chunk", spy_rebuild)

    renderer.pan_camera(3, 0)
    renderer.draw_world()

    assert rebuilds == []

    renderer.pan_camera(13, 0)
    renderer.draw_world()

    assert rebuilds == [(5, 0), (5, 1), (5, 2)]


def test_role_colors_are_bright_for_screensaver_readability():
    for role in (GENERALIST, FORAGER, BUILDER, SCOUT):
        color = color_for_role(role)

        assert max(color) >= 175
        assert sum(color) >= 330


def test_selected_agent_details_use_compact_villager_summary(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Eli", 1, 1, role=SCOUT, current_action="Wandering")
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

    assert ("Agent", "Eli") in rows
    assert ("Role", SCOUT) in rows
    assert ("State", "Exploring") in rows
    assert ("Action", "Wandering") in rows
    assert ("Details", "Open Villagers overlay") in rows


def test_selected_agent_details_omit_deep_villager_fields(monkeypatch):
    world = make_world(width=3, height=3)
    agent = Agent("Cato", 1, 1, lifecycle_stage="Elder", trait="Curious")
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

    assert not any(label in ("Life", "Trait", "Knows", "Needs", "Carry", "Path", "Idle") for label, _ in rows)


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


def test_time_grid_contains_year_day_and_speed():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    rows = renderer.time_grid_rows(sim_speed=4)

    assert rows == [
        ("Year", world.year),
        ("Day", world.day),
        ("Speed", "4x"),
    ]


def test_day_progress_bar_draws_seasonal_phase_segments():
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)

    renderer.draw_day_progress_bar(10, 10, 100, 100)

    morning_pixel = renderer.screen.get_at((16, 15))[:3]
    day_pixel = renderer.screen.get_at((35, 15))[:3]

    assert morning_pixel == PHASE_BAR_COLORS["morning"]
    assert day_pixel == PHASE_BAR_COLORS["day"]


def test_time_header_draws_season_phase_and_numeric_context(monkeypatch):
    world = make_world(width=3, height=3)
    renderer = make_renderer(world)
    lines = []

    def spy_draw_text_line(text, x, y, width, bottom_y, font=None, color=None):
        lines.append(str(text))
        return y + 1

    monkeypatch.setattr(renderer, "draw_text_line", spy_draw_text_line)
    monkeypatch.setattr(renderer, "draw_section_header", lambda text, x, y, width, bottom_y: spy_draw_text_line(text, x, y, width, bottom_y))

    renderer.draw_time_header(10, 10, 200, 200, sim_speed=4)

    assert "Time" in lines
    assert f"Season: {world.season_label}" in lines
    assert any("Morning" in line for line in lines)
    assert "Year: 1" in lines
    assert "Day: 1" in lines


def test_colony_summary_uses_compact_population_without_capacity_denominator():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent(f"A{i}", i, 1) for i in range(9)]
    world.settlement.carrying_capacity_report = CarryingCapacityReport(
        population=9,
        capacity=12,
        status="Stable",
        reason="Current housing, food, and water can support the living population.",
    )
    renderer = make_renderer(world)

    lines = renderer.colony_summary_lines()
    summary = "\n".join(lines)

    assert "Pop      9" in lines
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
        reason="Current housing, food, and water can support the living population.",
    )
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Center" not in summary
    assert "Rad" not in summary
    assert "Claims" not in summary
    assert "Cap" not in summary
    assert "Settlement Growing Village" in summary
    assert "Age      0 Years" in summary


def test_colony_summary_omits_planner_diagnostics_and_targets():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent(f"A{i}", i, 1) for i in range(6)]
    world.tile_at(0, 2).kind = "home"
    world.colony_storage.deposit_food(3)
    world.colony_storage.deposit_water(2)
    world.colony_storage.deposit_wood(4)
    world.settlement.planned_demands = {
        "house_construction": 80,
        "wood_gathering": 40,
        "food_production": 20,
    }
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Priorities:" not in summary
    assert "Current Priorities:" not in summary
    assert "1. Housing" not in summary
    assert "3 / 18" not in summary
    assert "2 / 12" not in summary
    assert "Food     Stable" in summary or "Food     Low" in summary
    assert "Water    Stable" in summary or "Water    Low" in summary
    assert "Housing  Strained" in summary


def test_colony_summary_includes_household_statistics():
    world = create_world(seed=913, agent_count=45)
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Households " in summary
    assert "Avg Home " in summary


def test_colony_summary_resource_status_reports_stability_without_raw_targets():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.agents = [Agent(f"A{i}", i, 1) for i in range(4)]
    world.tile_at(0, 2).kind = "home"
    world.tile_at(1, 2).kind = "home"
    world.colony_storage.deposit_food(4)
    world.colony_storage.deposit_water(4)
    world.colony_storage.deposit_wood(20)
    world.settlement.local_food = {(1, 1), (2, 1), (3, 1), (4, 1)}
    world.settlement.local_water = {(1, 3), (2, 3), (3, 3), (4, 3)}
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Food     Stable" in summary
    assert "Water    Stable" in summary
    assert "Wood" not in summary
    assert "20 / 8" not in summary


def test_colony_summary_omits_seasonal_wild_food_diagnostics():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    world.settlement.local_food = {(1, 1), (2, 1)}
    renderer = make_renderer(world)

    assert "Wild Food 2 | Growing" not in renderer.colony_summary_lines()
    assert all("Wild Food" not in line for line in renderer.colony_summary_lines())

    world.season_index = 3
    assert all("Winter Dormant" not in line for line in renderer.colony_summary_lines())


def test_colony_summary_and_selection_show_agriculture_foundation_details(monkeypatch):
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    farm = FarmPlot(2, 2, food=3)
    farm.crop_state = FIELD_READY
    world.settlement.farm_plots.append(farm)
    world.colony_storage.seed_reserve = 7
    renderer = make_renderer(world)

    summary = "\n".join(renderer.colony_summary_lines())
    assert "Farms 1 | Seeds 7" not in summary
    assert "Seeds 7" not in summary

    renderer.selected_tile = (2, 2)
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 200, 200)

    assert ("Crop State", FIELD_READY) in rows
    assert ("Farm Food", 3) in rows


def test_selected_home_tile_shows_household_details(monkeypatch):
    world = create_world(seed=914, agent_count=45)
    home = world.settlement.homes[0]
    household = world.settlement.household_for_home(home.home_id)
    renderer = make_renderer(world)
    renderer.selected_tile = (home.x, home.y)
    rows = []

    def spy_draw_stat_row(label, value, x, y, width, bottom_y, color=None):
        rows.append((label, value))
        return y + 1

    monkeypatch.setattr(renderer, "draw_section_header", lambda *args, **kwargs: args[2])
    monkeypatch.setattr(renderer, "draw_stat_row", spy_draw_stat_row)

    renderer.draw_selection_details(0, 0, 220, 220)

    assert ("Home", home.home_id) in rows
    assert ("Household", household.household_name) in rows
    assert ("Founded Year", household.founded_year) in rows
    assert ("Household Age", household.established_years) in rows
    assert any(label == "Occupants" and str(len(household.member_ids)) in str(value) for label, value in rows)
    assert any(label == "House Size" and "Tile" in str(value) for label, value in rows)
    assert any(label == "Members" and value != "None" for label, value in rows)


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
        reason="Current housing, food, and water can support the living population.",
    )

    assert renderer.colony_reason_lines() == []


def test_colony_summary_omits_reason_text_even_when_strained():
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

    summary = "\n".join(renderer.colony_summary_lines())

    assert "Reason:" not in summary
    assert "Food stores low" not in summary
    assert "Few local food sources" not in summary


def test_colony_summary_handles_missing_capacity_report():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, founded_day=1, founded_season="Spring")
    renderer = make_renderer(world)

    lines = renderer.colony_summary_lines()

    assert "Pop      0" in lines
    assert "Food     Stocked" in lines
    assert "Water    Stocked" in lines
    assert "Housing  Stable" in lines


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
