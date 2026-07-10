import pygame
from dataclasses import dataclass, field
from typing import Callable

import pygame_gui
import time

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PANEL_WIDTH,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    TILE_SIZE,
    CAMERA_STEP,
    DEBUG_DRAW_GRID,
    COLORS,
    DAYS_PER_SEASON,
    TERRAIN_LABELS,
    FPS,
    PERFORMANCE_LOGGING,
    PERFORMANCE_LOG_INTERVAL_FRAMES,
    VILLAGER_RENDER_TILES_PER_SECOND,
    TASK_BUILD_TICKS,
    DESIRED_WOOD_RESERVE,
    SHELTER_CAPACITY,
    SETTLEMENT_FOOD_TARGET_DAYS,
    SETTLEMENT_WATER_TARGET_DAYS,
    SEASON_FOOD_GROWTH_MODIFIERS,
    SEASONS,
    TICKS_PER_DAY,
)
from src.environment_events import active_event_names
from src.farming import FIELD_DORMANT, FIELD_GROWING, FIELD_PLANTED, FIELD_READY, FIELD_UNPREPARED, farm_border_edges
from src.forest_rendering import FOREST_SEASON_PALETTES, forest_transition_cache_key
from src.grass_rendering import (
    GrassMoistureTransitionState,
    grass_moisture_mode_for_events,
)
from src.overlays.diagnostics import DIAGNOSTICS_OVERLAY, DiagnosticsOverlay
from src.overlays.history import HISTORY_OVERLAY, HistoryOverlay
from src.overlays.villagers import VILLAGERS_OVERLAY, VillagersOverlay
from src.resource_ecology import max_food, max_wood
from src.role_colors import color_for_role
from src.seasons import seasonal_tile_color
from src.task_behavior import (
    PHASE_DAY,
    PHASE_EVENING,
    PHASE_MORNING,
    PHASE_NIGHT,
    day_progress,
    phase_progress_segments,
    settlement_phase_label,
    village_phase,
)
from src.terrain_rendering import (
    GameplayVisualState,
    TerrainNeighbourhood,
    TerrainRenderContext,
    TerrainRenderer,
    TerrainVisualModifier,
    construction_visual_stage,
    crop_visual_stage,
)
from src.agent import Agent
from src.presentation import PresentationAgentSnapshot, PresentationScene
from src.profiler import profiler
from src.simulation_lod import LOD_0_VISUAL
from src.ui_overlays import OverlayManager
from src.village_paths import path_border_edges
from src.villager_inspection import compact_villager_rows
from src.water_rendering import (
    WaterTransitionState,
    weather_state_for_events,
)
from src.workplace import FARM, STORAGE, VILLAGE_CENTER, WORKSHOP
from src.world import World

TERRAIN_CHUNK_SIZE = 16


@dataclass
class TerrainChunkCache:
    chunk_x: int
    chunk_y: int
    surface: pygame.Surface
    cache_state: tuple[object, ...] | None = None
    visual_revision: int = 0
    dirty: bool = True
    full_dirty: bool = True
    dirty_tiles: set[tuple[int, int]] = field(default_factory=set)
    last_redraw_count: int = 0


@dataclass(frozen=True)
class RendererLayer:
    name: str
    owner: str
    draw: Callable[[], None]
    cached: bool = False


def average_color(colors: tuple[tuple[int, int, int], ...]) -> tuple[int, int, int]:
    count = max(1, len(colors))
    return (
        round(sum(color[0] for color in colors) / count),
        round(sum(color[1] for color in colors) / count),
        round(sum(color[2] for color in colors) / count),
    )


def mix_color(color_a: tuple[int, int, int], color_b: tuple[int, int, int], progress: float) -> tuple[int, int, int]:
    progress = max(0.0, min(1.0, progress))
    return tuple(
        round(start + (end - start) * progress)
        for start, end in zip(color_a, color_b)
    )


def is_food_visible_to_player(world: World, x: int, y: int) -> bool:
    return (x, y) in world.colony_memory.known_food


def is_wood_visible_to_player(world: World, x: int, y: int) -> bool:
    return (x, y) in world.colony_memory.known_wood


def _planner_label(name: str) -> str:
    labels = {
        "food_production": "Food",
        "farming": "Farming",
        "water_collection": "Water",
        "wood_gathering": "Wood",
        "house_construction": "Housing",
        "exploration": "Exploration",
        "village_support": "Support",
    }
    return labels.get(name, name.replace("_", " ").title())


PHASE_ICONS = {
    PHASE_MORNING: "[/]",
    PHASE_DAY: "[*]",
    PHASE_EVENING: r"[\]",
    PHASE_NIGHT: "[C]",
}

PHASE_BAR_COLORS = {
    PHASE_MORNING: (188, 132, 78),
    PHASE_DAY: (218, 186, 82),
    PHASE_EVENING: (154, 104, 98),
    PHASE_NIGHT: (62, 72, 116),
}


VILLAGER_TILE_OFFSETS = (
    (0, 0),
    (-4, -4),
    (4, -4),
    (-4, 4),
    (4, 4),
    (0, -5),
    (-5, 0),
    (5, 0),
    (0, 5),
)


class PygameRenderer:
    def __init__(self, world: World):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")
        self.ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay_manager = OverlayManager()
        self.register_overlays()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 13)
        self.big_font = pygame.font.SysFont("consolas", 17, bold=True)

        self.selected_agent: Agent | None = None
        self.selected_tile: tuple[int, int] | None = None
        self.panel_padding = 14
        self.panel_gap = 8
        self.presentation_scene = PresentationScene()
        self.configure_observer_camera()
        self.camera_x = 0
        self.camera_y = 0
        self.map_surface = pygame.Surface((VIEWPORT_WIDTH * TILE_SIZE, VIEWPORT_HEIGHT * TILE_SIZE)).convert()
        self.map_cache_key = None
        self.map_visual_transition_key = None
        self.map_dynamic_visual_key = None
        self.terrain_chunks: dict[tuple[int, int], TerrainChunkCache] = {}
        self.dirty_chunks: set[tuple[int, int]] = set()
        self.tile_visual_cache: dict[tuple[int, int], tuple[object, ...]] = {}
        self.renderer_revisions = {
            "terrain": 0,
            "weather": 0,
            "season": 0,
            "moisture": 0,
            "construction": 0,
            "overlays": 0,
        }
        self.last_partial_redraw_count = 0
        self.last_chunk_rebuild_count = 0
        self.last_chunk_redraw_count = 0
        self._draw_target = self.screen
        self._agent_tile_counts: dict[tuple[int, int], int] = {}
        self._agent_tile_drawn: dict[tuple[int, int], int] = {}
        self.terrain_renderer = TerrainRenderer()
        self.grass_transition_state = GrassMoistureTransitionState()
        self.water_transition_state = WaterTransitionState()
        self.presentation_scene.sync_world(world)
        self.presentation_engine = self.presentation_scene
        self.frame_count = 0
        self.last_render_ms = 0.0
        self.last_sim_ms = 0.0
        self.last_sim_ticks = 0
        self.current_paused = False
        self.current_sim_speed = 0
        self.render_layers: tuple[RendererLayer, ...] = ()
        self.configure_render_layers()

    def register_overlays(self):
        self.overlay_manager.register_overlay(
            VILLAGERS_OVERLAY,
            lambda: VillagersOverlay(
                self.world,
                self.ui_manager,
                self.select_agent,
                self.selected_villager,
            ),
        )
        self.overlay_manager.register_overlay(
            HISTORY_OVERLAY,
            lambda: HistoryOverlay(
                self.world,
                self.ui_manager,
            ),
        )

    def configure_render_layers(self) -> None:
        self.render_layers = (
            RendererLayer("Terrain", "TerrainLayer", self.draw_terrain_layer, cached=True),
            RendererLayer("Vegetation", "VegetationLayer", self.draw_vegetation_layer),
            RendererLayer("Structures", "StructureLayer", self.draw_structure_layer, cached=True),
            RendererLayer("Environment", "EnvironmentalOverlayLayer", self.draw_environmental_overlay_layer),
            RendererLayer("Agents", "AgentLayer", self.draw_agent_layer),
            RendererLayer("Effects", "EffectsLayer", self.draw_effects_layer),
            RendererLayer("UI", "UILayer", self.draw_ui_layer),
        )
        self.overlay_manager.register_overlay(
            DIAGNOSTICS_OVERLAY,
            lambda: DiagnosticsOverlay(
                self.world,
                self.ui_manager,
                self.diagnostics_metrics,
            ),
        )

    def configure_observer_camera(self) -> None:
        self.presentation_scene.configure_camera(
            world_width=self.world.width,
            world_height=self.world.height,
            viewport_width=VIEWPORT_WIDTH,
            viewport_height=VIEWPORT_HEIGHT,
        )

    @property
    def observer_camera(self):
        return self.presentation_scene.observer_camera

    @property
    def camera_x(self) -> int:
        return int(self.observer_camera.target_x)

    @camera_x.setter
    def camera_x(self, value: int | float) -> None:
        if not hasattr(self, "presentation_scene"):
            self._legacy_camera_x = value
            return
        self.observer_camera.set_position(
            value,
            self.observer_camera.target_y,
            snap=True,
            clamp=False,
        )

    @property
    def camera_y(self) -> int:
        return int(self.observer_camera.target_y)

    @camera_y.setter
    def camera_y(self, value: int | float) -> None:
        if not hasattr(self, "presentation_scene"):
            self._legacy_camera_y = value
            return
        self.observer_camera.set_position(
            self.observer_camera.target_x,
            value,
            snap=True,
            clamp=False,
        )

    def set_world(self, world: World):
        self.world = world
        self.grass_transition_state = GrassMoistureTransitionState()
        self.water_transition_state = WaterTransitionState()
        self.presentation_scene = PresentationScene()
        self.configure_observer_camera()
        self.presentation_scene.sync_world(world)
        self.presentation_engine = self.presentation_scene
        self.clear_selection()
        self.overlay_manager.close_all()
        self.clamp_camera()
        self.invalidate_map_cache()

    def invalidate_map_cache(self):
        self.map_cache_key = None
        self.map_visual_transition_key = None
        self.map_dynamic_visual_key = None
        self.tile_visual_cache.clear()
        self.terrain_chunks.clear()
        self.dirty_chunks.clear()
        self.bump_renderer_revision("terrain")

    def bump_renderer_revision(self, name: str) -> None:
        self.renderer_revisions[name] = self.renderer_revisions.get(name, 0) + 1

    def process_ui_event(self, event) -> bool:
        overlay_consumed = self.overlay_manager.handle_event(event)
        gui_consumed = self.ui_manager.process_events(event)
        return overlay_consumed or gui_consumed

    def update_ui(self, time_delta: float, paused: bool = False):
        self.update_presentation(time_delta, paused=paused)
        self.overlay_manager.update(time_delta)
        self.ui_manager.update(time_delta)

    def update_presentation(self, time_delta: float, paused: bool = False):
        self.presentation_scene.update(
            self.world,
            time_delta,
            VILLAGER_RENDER_TILES_PER_SECOND,
            paused=paused,
        )

    def update_agent_render_motion(self, time_delta: float):
        self.update_presentation(time_delta)

    def toggle_villagers_overlay(self):
        self.overlay_manager.toggle_overlay(VILLAGERS_OVERLAY)

    def toggle_history_overlay(self):
        self.overlay_manager.toggle_overlay(HISTORY_OVERLAY)

    def toggle_diagnostics_overlay(self):
        self.overlay_manager.toggle_overlay(DIAGNOSTICS_OVERLAY)

    def diagnostics_metrics(self) -> dict[str, object]:
        return {
            "last_render_ms": self.last_render_ms,
            "last_sim_ms": self.last_sim_ms,
            "sim_ticks": self.last_sim_ticks,
            "fps": self.clock.get_fps(),
            "render_layers": tuple(layer.name for layer in self.render_layers),
            "terrain_chunks": len(self.terrain_chunks),
            "dirty_chunks": len(self.dirty_chunks),
            "last_chunk_rebuilds": self.last_chunk_rebuild_count,
            "last_chunk_redraws": self.last_chunk_redraw_count,
            "last_partial_redraws": self.last_partial_redraw_count,
            "presentation_agents": len(self.presentation_scene.agents),
            "presentation_frame": self.presentation_scene.presentation_time.frame_index,
            "presentation_time": round(self.presentation_scene.presentation_time.elapsed_seconds, 3),
        }

    def selected_villager(self):
        return self.selected_agent

    def select_agent(self, agent: Agent):
        if agent not in self.world.agents:
            self.clear_selection()
            return
        self.selected_agent = agent
        self.selected_tile = None

    def select_tile_at_pixel(self, mouse_x: int, mouse_y: int):
        tile = self.screen_to_world_tile(mouse_x, mouse_y)
        if tile is None:
            self.clear_selection()
            return

        tile_x, tile_y = tile
        self.select_tile(tile_x, tile_y)

    def screen_to_world_tile(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        map_width = VIEWPORT_WIDTH * TILE_SIZE
        map_height = VIEWPORT_HEIGHT * TILE_SIZE
        if not (0 <= mouse_x < map_width and 0 <= mouse_y < map_height):
            return None

        return (
            self.observer_camera.screen_to_tile(mouse_x, mouse_y, TILE_SIZE)
        )

    def camera_step(self) -> int:
        return CAMERA_STEP

    def pan_camera(self, dx: int, dy: int):
        self.observer_camera.pan_by(dx, dy, snap=True)
        self.clamp_camera()

    def clamp_camera(self):
        self.configure_observer_camera()
        self.observer_camera.set_position(
            self.observer_camera.target_x,
            self.observer_camera.target_y,
            snap=True,
        )

    def visible_tile_bounds(self) -> tuple[int, int, int, int]:
        self.clamp_camera()
        return self.observer_camera.visible_tile_bounds()

    def select_tile(self, tile_x: int, tile_y: int):
        if not (0 <= tile_x < self.world.width and 0 <= tile_y < self.world.height):
            self.clear_selection()
            return

        agent = self.world.agent_at(tile_x, tile_y)
        if agent is not None:
            self.select_agent(agent)
            return

        self.selected_agent = None
        self.selected_tile = (tile_x, tile_y)

    def clear_selection(self):
        self.selected_agent = None
        self.selected_tile = None

    def validate_selection(self):
        if self.selected_agent is not None and self.selected_agent not in self.world.agents:
            self.clear_selection()

        if self.selected_tile is not None:
            x, y = self.selected_tile
            if not (0 <= x < self.world.width and 0 <= y < self.world.height):
                self.clear_selection()

    def draw(self, paused: bool, sim_speed: int, last_sim_ms: float = 0.0, sim_ticks: int = 0):
        with profiler.time("renderer update"):
            render_start = time.perf_counter()
            self.last_sim_ms = last_sim_ms
            self.last_sim_ticks = sim_ticks
            self.current_paused = paused
            self.current_sim_speed = sim_speed
            self.validate_selection()
            self.clamp_camera()
            self.screen.fill((0, 0, 0))

            self.compose_scene()

            pygame.display.flip()
            self.frame_count += 1
            self.last_render_ms = (time.perf_counter() - render_start) * 1000
            if PERFORMANCE_LOGGING and self.frame_count % PERFORMANCE_LOG_INTERVAL_FRAMES == 0:
                print(
                    f"perf render frame={self.frame_count} paused={paused} speed={sim_speed} "
                    f"render_ms={self.last_render_ms:.2f} sim_ms={last_sim_ms:.2f} sim_ticks={sim_ticks} "
                    f"world_tick_ms={self.world.last_tick_ms:.2f} "
                    f"villager_ms={self.world.last_villager_ms:.2f} "
                    f"path_calls={self.world.pathfinding_calls}"
                )
            if hasattr(self.world, "record_lod_update"):
                elapsed_seconds = time.perf_counter() - render_start
                self.world.record_lod_update(LOD_0_VISUAL, elapsed_seconds)

    def draw_world(self):
        self.draw_terrain_layer()
        self.draw_vegetation_layer()
        self.draw_structure_layer()
        self.draw_environmental_overlay_layer()
        self.draw_agent_layer()
        self.draw_effects_layer()
        self.draw_selection_highlight()

    def compose_scene(self) -> None:
        for layer in self.render_layers:
            with profiler.time(f"renderer layer {layer.name}"):
                layer.draw()

    def draw_terrain_layer(self) -> None:
        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        self.draw_cached_map(start_x, start_y, end_x, end_y)

    def draw_vegetation_layer(self) -> None:
        self.draw_forest_foliage_overlay()

    def draw_structure_layer(self) -> None:
        # Static structures are currently cached during chunk rebuilds to preserve existing visuals.
        return

    def draw_forest_foliage_overlay(self) -> None:
        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        foliage_tiles = [
            (x, y)
            for y in range(start_y, end_y)
            for x in range(start_x, end_x)
            if self.world.tile_at(x, y).kind == "forest"
        ]
        if not foliage_tiles:
            return

        color = self.smooth_foliage_color()
        overlay = pygame.Surface((VIEWPORT_WIDTH * TILE_SIZE, VIEWPORT_HEIGHT * TILE_SIZE), pygame.SRCALPHA)
        tint = (*color, 34)
        highlight = (min(255, color[0] + 18), min(255, color[1] + 18), min(255, color[2] + 18), 24)
        for x, y in foliage_tiles:
            screen_x = (x - start_x) * TILE_SIZE
            screen_y = (y - start_y) * TILE_SIZE
            pygame.draw.ellipse(overlay, tint, pygame.Rect(screen_x + 1, screen_y + 1, TILE_SIZE - 2, TILE_SIZE - 2))
            if (x * 17 + y * 31 + getattr(self.world, "tick", 0) // 12) % 5 == 0:
                pygame.draw.circle(overlay, highlight, (screen_x + TILE_SIZE // 2, screen_y + TILE_SIZE // 3), max(1, TILE_SIZE // 5))
        self.screen.blit(overlay, (0, 0))

    def smooth_foliage_color(self) -> tuple[int, int, int]:
        season_index = getattr(self.world, "season_index", 0)
        day_fraction = (getattr(self.world, "day_of_season", 1) - 1) + (
            getattr(self.world, "ticks_into_day", 0) / max(1, TICKS_PER_DAY)
        )
        progress = max(0.0, min(1.0, day_fraction / max(1, DAYS_PER_SEASON)))
        current_season = SEASONS[season_index % len(SEASONS)]
        next_season = SEASONS[(season_index + 1) % len(SEASONS)]
        return mix_color(
            average_color(FOREST_SEASON_PALETTES[current_season]),
            average_color(FOREST_SEASON_PALETTES[next_season]),
            progress,
        )

    def draw_environmental_overlay_layer(self) -> None:
        self.draw_cloud_shadow_overlay()
        self.draw_mystery_lights_overlay()

    def draw_agent_layer(self) -> None:
        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        self.draw_agents(start_x, start_y, end_x, end_y)

    def draw_effects_layer(self) -> None:
        self.draw_weather_particles()

    def draw_ui_layer(self) -> None:
        self.draw_selection_highlight()
        self.draw_panel(getattr(self, "current_paused", False), getattr(self, "current_sim_speed", 0))
        self.ui_manager.draw_ui(self.screen)

    def map_cache_state(self, start_x: int, start_y: int, end_x: int, end_y: int):
        return (
            self.world.width,
            self.world.height,
            self.terrain_renderer.detail_level,
            self.terrain_renderer.microtile_grid.resolution,
        )

    def dynamic_visual_cache_state(self):
        settlement = self.world.settlement
        return (
            self.gameplay_visual_cache_state(),
            len(self.world.colony_memory.known_food),
            len(self.world.colony_memory.known_wood),
            len(settlement.farm_plots) if settlement is not None else 0,
            len(settlement.stockpiles) if settlement is not None else 0,
            len(settlement.workshops) if settlement is not None else 0,
            len(settlement.homes) if settlement is not None else 0,
            len(settlement.workplaces) if settlement is not None else 0,
        )

    def visual_transition_cache_state(self):
        return (
            forest_transition_cache_key(self.world),
            self.world.season,
            self.world.next_season,
            round(getattr(self.world, "visual_transition_progress", self.world.transition_progress), 3),
        )

    def gameplay_visual_cache_state(self):
        settlement = self.world.settlement
        if settlement is None:
            return ()
        farm_state = tuple(
            sorted(
                (
                    farm.origin_x,
                    farm.origin_y,
                    farm.crop_state,
                    farm.growth,
                    farm.food,
                    round(farm.fertility, 2),
                )
                for farm in settlement.farm_plots
                if farm.active
            )
        )
        construction_state = tuple(sorted(settlement.construction_progress.items()))
        return (farm_state, construction_state)

    def update_grass_transition_state(self):
        self.grass_transition_state.update(
            grass_moisture_mode_for_events(self.world.active_environment_events),
            self.world.tick,
        )

    def update_water_transition_state(self):
        self.water_transition_state.update(
            weather_state_for_events(self.world.active_environment_events),
            self.world.tick,
        )

    def environment_event_cache_state(self):
        return tuple(
            sorted(
                (
                    getattr(event, "effect_type", None),
                    getattr(event, "remaining_days", None),
                )
                for event in self.world.active_environment_events
            )
        )

    def environmental_overlay_state(self) -> tuple[object, ...]:
        effects = tuple(
            sorted(getattr(event, "effect_type", None) for event in self.world.active_environment_events)
        )
        mysteries = tuple(
            sorted(
                (
                    getattr(mystery, "mystery_type", None),
                    getattr(mystery, "anchor", None),
                    getattr(mystery, "remaining_days", None),
                )
                for mystery in getattr(self.world, "active_mysteries", [])
            )
        )
        cloud_offset = (getattr(self.world, "tick", 0) // 6) % max(1, TILE_SIZE * 8)
        particle_offset = getattr(self.world, "tick", 0) % max(1, TILE_SIZE * 3)
        return (effects, mysteries, cloud_offset, particle_offset)

    def draw_cloud_shadow_overlay(self) -> None:
        effects = {getattr(event, "effect_type", None) for event in self.world.active_environment_events}
        if not effects & {"heavy_rain", "rain", "fog"}:
            return
        width = VIEWPORT_WIDTH * TILE_SIZE
        height = VIEWPORT_HEIGHT * TILE_SIZE
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        offset = (getattr(self.world, "tick", 0) // 6) % max(1, TILE_SIZE * 8)
        shadow_color = (12, 18, 24, 24 if "heavy_rain" in effects else 16)
        for index in range(-2, VIEWPORT_WIDTH + 8, 7):
            x = index * TILE_SIZE - offset
            y = ((index * 5 + getattr(self.world, "tick", 0) // 18) % (VIEWPORT_HEIGHT + 6) - 3) * TILE_SIZE
            pygame.draw.ellipse(overlay, shadow_color, pygame.Rect(x, y, TILE_SIZE * 7, TILE_SIZE * 3))
        self.screen.blit(overlay, (0, 0))

    def draw_mystery_lights_overlay(self) -> None:
        mysteries = [
            mystery
            for mystery in getattr(self.world, "active_mysteries", [])
            if getattr(mystery, "mystery_type", None) == "strange_lights"
        ]
        if not mysteries:
            return

        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        overlay = pygame.Surface((VIEWPORT_WIDTH * TILE_SIZE, VIEWPORT_HEIGHT * TILE_SIZE), pygame.SRCALPHA)
        tick = getattr(self.world, "tick", 0)
        for mystery in mysteries:
            ax, ay = mystery.anchor
            if not (start_x - 2 <= ax < end_x + 2 and start_y - 2 <= ay < end_y + 2):
                continue
            base_x = (ax - start_x) * TILE_SIZE + TILE_SIZE // 2
            base_y = (ay - start_y) * TILE_SIZE + TILE_SIZE // 2
            for index in range(7):
                drift_x = ((tick // 3 + index * 11) % 17) - 8
                drift_y = ((tick // 5 + index * 7) % 13) - 6
                pulse = 38 + ((tick + index * 19) % 30)
                x = base_x + drift_x + (index % 3 - 1) * 6
                y = base_y + drift_y + (index // 3 - 1) * 5
                pygame.draw.circle(overlay, (172, 216, 190, 24), (x, y), 8)
                pygame.draw.circle(overlay, (210, 242, 214, pulse), (x, y), 2)
        self.screen.blit(overlay, (0, 0))

    def draw_weather_particles(self) -> None:
        effects = {getattr(event, "effect_type", None) for event in self.world.active_environment_events}
        if "heavy_rain" not in effects:
            return
        width = VIEWPORT_WIDTH * TILE_SIZE
        height = VIEWPORT_HEIGHT * TILE_SIZE
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        tick = getattr(self.world, "tick", 0)
        for index in range(36):
            x = (index * 37 + tick * 2) % max(1, width)
            y = (index * 23 + tick * 5) % max(1, height)
            pygame.draw.line(overlay, (132, 164, 204, 92), (x, y), (x - 2, y + 6), 1)
        self.screen.blit(overlay, (0, 0))

    def draw_cached_map(self, start_x: int, start_y: int, end_x: int, end_y: int):
        cache_key = self.map_cache_state(start_x, start_y, end_x, end_y)
        visual_key = self.visual_transition_cache_state()
        dynamic_key = self.dynamic_visual_cache_state()
        self.last_partial_redraw_count = 0
        self.last_chunk_rebuild_count = 0
        self.last_chunk_redraw_count = 0
        if cache_key != self.map_cache_key:
            self.mark_all_chunks_dirty()
            self.map_cache_key = cache_key
            self.map_visual_transition_key = visual_key
            self.map_dynamic_visual_key = dynamic_key
            self.bump_renderer_revision("terrain")
        elif visual_key != self.map_visual_transition_key:
            self.mark_visual_transition_revisions(self.map_visual_transition_key, visual_key)
            self.redraw_dirty_visible_tiles(start_x, start_y, end_x, end_y)
            self.map_visual_transition_key = visual_key
        elif dynamic_key != self.map_dynamic_visual_key:
            self.mark_dynamic_visual_revisions(self.map_dynamic_visual_key, dynamic_key)
            self.redraw_dirty_visible_tiles(start_x, start_y, end_x, end_y)
            self.map_dynamic_visual_key = dynamic_key
        self.draw_visible_chunks(start_x, start_y, end_x, end_y)

    def mark_all_chunks_dirty(self) -> None:
        for chunk in self.terrain_chunks.values():
            chunk.dirty = True
            chunk.full_dirty = True
            chunk.dirty_tiles.clear()
            self.dirty_chunks.add((chunk.chunk_x, chunk.chunk_y))

    def mark_dynamic_visual_revisions(self, old_key, new_key) -> None:
        if old_key is None:
            self.bump_renderer_revision("terrain")
            return
        if old_key[0] != new_key[0]:
            self.bump_renderer_revision("construction")
        if old_key[1:] != new_key[1:]:
            self.bump_renderer_revision("overlays")

    def draw_visible_chunks(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, 0, VIEWPORT_WIDTH * TILE_SIZE, VIEWPORT_HEIGHT * TILE_SIZE))
        for chunk_x, chunk_y in self.visible_chunk_coords(start_x, start_y, end_x, end_y):
            chunk = self.chunk_for(chunk_x, chunk_y)
            if chunk.dirty:
                self.rebuild_chunk(chunk)
            blit_x = chunk_x * TERRAIN_CHUNK_SIZE * TILE_SIZE - start_x * TILE_SIZE
            blit_y = chunk_y * TERRAIN_CHUNK_SIZE * TILE_SIZE - start_y * TILE_SIZE
            self.screen.blit(chunk.surface, (blit_x, blit_y))
        self.screen.set_clip(previous_clip)

    def visible_chunk_coords(self, start_x: int, start_y: int, end_x: int, end_y: int):
        first_chunk_x = start_x // TERRAIN_CHUNK_SIZE
        first_chunk_y = start_y // TERRAIN_CHUNK_SIZE
        last_chunk_x = (max(start_x, end_x - 1)) // TERRAIN_CHUNK_SIZE
        last_chunk_y = (max(start_y, end_y - 1)) // TERRAIN_CHUNK_SIZE
        for chunk_y in range(first_chunk_y, last_chunk_y + 1):
            for chunk_x in range(first_chunk_x, last_chunk_x + 1):
                yield chunk_x, chunk_y

    def chunk_for(self, chunk_x: int, chunk_y: int) -> TerrainChunkCache:
        key = (chunk_x, chunk_y)
        chunk = self.terrain_chunks.get(key)
        if chunk is None:
            surface = pygame.Surface(
                (
                    TERRAIN_CHUNK_SIZE * TILE_SIZE,
                    TERRAIN_CHUNK_SIZE * TILE_SIZE,
                )
            ).convert()
            chunk = TerrainChunkCache(chunk_x, chunk_y, surface)
            self.terrain_chunks[key] = chunk
        return chunk

    def rebuild_chunk(self, chunk: TerrainChunkCache) -> None:
        previous_target = self._draw_target
        self._draw_target = chunk.surface
        chunk.last_redraw_count = 0
        start_x = chunk.chunk_x * TERRAIN_CHUNK_SIZE
        start_y = chunk.chunk_y * TERRAIN_CHUNK_SIZE
        end_x = min(self.world.width, start_x + TERRAIN_CHUNK_SIZE)
        end_y = min(self.world.height, start_y + TERRAIN_CHUNK_SIZE)

        if chunk.full_dirty or chunk.cache_state is None:
            chunk.surface.fill((0, 0, 0))
            tiles_to_draw = tuple(
                (x, y)
                for y in range(start_y, end_y)
                for x in range(start_x, end_x)
            )
        else:
            tiles_to_draw = tuple(
                (x, y)
                for x, y in chunk.dirty_tiles
                if start_x <= x < end_x and start_y <= y < end_y
            )

        for x, y in tiles_to_draw:
            self.draw_map_tile(x, y, start_x, start_y)
            chunk.last_redraw_count += 1
        self._draw_target = previous_target
        chunk.cache_state = self.chunk_cache_state(chunk)
        chunk.visual_revision += 1
        chunk.dirty = False
        chunk.full_dirty = False
        chunk.dirty_tiles.clear()
        self.dirty_chunks.discard((chunk.chunk_x, chunk.chunk_y))
        self.last_chunk_rebuild_count += 1
        self.last_chunk_redraw_count += chunk.last_redraw_count

    def chunk_cache_state(self, chunk: TerrainChunkCache) -> tuple[object, ...]:
        return (
            self.map_cache_key,
            self.map_visual_transition_key,
            self.map_dynamic_visual_key,
            chunk.visual_revision,
        )

    def mark_visual_transition_revisions(self, old_key, new_key) -> None:
        if old_key is None:
            self.bump_renderer_revision("terrain")
            return
        if old_key != new_key:
            self.bump_renderer_revision("season")

    def rebuild_map_surface(self, start_x: int, start_y: int, end_x: int, end_y: int):
        previous_target = self._draw_target
        self._draw_target = self.map_surface
        self.map_surface.fill((0, 0, 0))
        self.tile_visual_cache.clear()
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                self.draw_map_tile(x, y, start_x, start_y)
        self._draw_target = previous_target

    def redraw_dirty_visible_tiles(self, start_x: int, start_y: int, end_x: int, end_y: int) -> int:
        redraws = 0
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                signature = self.tile_render_signature(x, y)
                if self.tile_visual_cache.get((x, y)) == signature:
                    continue
                self.mark_tile_dirty(x, y)
                self.tile_visual_cache[(x, y)] = signature
                redraws += 1
        self.last_partial_redraw_count = redraws
        return redraws

    def mark_tile_dirty(self, tile_x: int, tile_y: int) -> None:
        chunk_x = tile_x // TERRAIN_CHUNK_SIZE
        chunk_y = tile_y // TERRAIN_CHUNK_SIZE
        chunk = self.terrain_chunks.get((chunk_x, chunk_y))
        if chunk is not None:
            chunk.dirty = True
            if not chunk.full_dirty:
                chunk.dirty_tiles.add((tile_x, tile_y))
        self.dirty_chunks.add((chunk_x, chunk_y))

    def mark_tile_and_neighbours_dirty(self, tile_x: int, tile_y: int) -> None:
        for y in range(max(0, tile_y - 1), min(self.world.height, tile_y + 2)):
            for x in range(max(0, tile_x - 1), min(self.world.width, tile_x + 2)):
                self.mark_tile_dirty(x, y)

    def draw_map_tile(
        self,
        x: int,
        y: int,
        start_x: int,
        start_y: int,
        signature: tuple[object, ...] | None = None,
    ) -> None:
        tile = self.world.tile_at(x, y)
        screen_x = x - start_x
        screen_y = y - start_y

        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )

        self.draw_terrain_chunk_tile(x, y, rect)
        self.draw_vegetation_chunk_tile(x, y, screen_x, screen_y)
        self.draw_structure_chunk_tile(x, y, screen_x, screen_y, tile)

        self.tile_visual_cache[(x, y)] = signature or self.tile_render_signature(x, y)

    def draw_terrain_chunk_tile(self, x: int, y: int, rect: pygame.Rect) -> None:
        self.terrain_renderer.draw_tile(self._draw_target, rect, self.terrain_render_context(x, y))
        if DEBUG_DRAW_GRID:
            pygame.draw.rect(self._draw_target, COLORS["grid"], rect, 1)

    def draw_vegetation_chunk_tile(self, x: int, y: int, screen_x: int, screen_y: int) -> None:
        return

    def draw_structure_chunk_tile(self, x: int, y: int, screen_x: int, screen_y: int, tile) -> None:
        workplace = self.world.workplace_at(x, y)
        if workplace is not None:
            self.draw_workplace_placeholder(workplace, screen_x, screen_y, x, y)

        farm = self.world.farm_at(x, y)
        if farm is not None:
            self.draw_farm_border(farm, screen_x, screen_y, x, y)
            self.draw_farm_state_symbol(farm, screen_x, screen_y)

        if tile.food > 0 and is_food_visible_to_player(self.world, x, y):
            self.draw_centered_symbol("f", screen_x, screen_y, self.resource_color("food", tile.food, max_food(tile)))

        if tile.wood > 0 and is_wood_visible_to_player(self.world, x, y):
            self.draw_centered_symbol("w", screen_x, screen_y, self.resource_color("wood", tile.wood, max_wood(tile)))

        animal = self.world.animal_at(x, y)
        if animal:
            self.draw_centered_symbol(animal.symbol, screen_x, screen_y, COLORS["wildlife"])

        if self.is_settlement_center(x, y):
            self.draw_centered_symbol("+", screen_x, screen_y, COLORS["settlement"])

        if self.world.home_at(x, y):
            self.draw_centered_symbol("H", screen_x, screen_y, COLORS["text"])

        stockpile = self.world.stockpile_at(x, y)
        if stockpile:
            symbol = "F" if stockpile.stockpile_type == "food" else "W"
            color = COLORS["stockpile_food"] if stockpile.stockpile_type == "food" else COLORS["stockpile_wood"]
            self.draw_centered_symbol(symbol, screen_x, screen_y, color)

        workshop = self.world.workshop_at(x, y)
        if workshop:
            self.draw_centered_symbol("T", screen_x, screen_y, COLORS["workshop"])

    def tile_render_signature(self, tile_x: int, tile_y: int) -> tuple[object, ...]:
        tile = self.world.tile_at(tile_x, tile_y)
        context = self.terrain_render_context(tile_x, tile_y)
        visual_state = self.terrain_renderer.visual_state_for(context)
        return (
            visual_state,
            context.neighbourhood.kinds if context.neighbourhood is not None else (),
            self.tile_overlay_signature(tile_x, tile_y, tile),
        )

    def tile_overlay_signature(self, tile_x: int, tile_y: int, tile) -> tuple[object, ...]:
        farm = self.world.farm_at(tile_x, tile_y)
        animal = self.world.animal_at(tile_x, tile_y)
        stockpile = self.world.stockpile_at(tile_x, tile_y)
        workplace = self.world.workplace_at(tile_x, tile_y)
        workshop = self.world.workshop_at(tile_x, tile_y)
        return (
            tile.kind,
            tile.food if is_food_visible_to_player(self.world, tile_x, tile_y) else None,
            tile.wood if is_wood_visible_to_player(self.world, tile_x, tile_y) else None,
            getattr(tile, "foot_traffic", 0),
            getattr(tile, "walkable", True),
            getattr(animal, "symbol", None),
            self.is_settlement_center(tile_x, tile_y),
            bool(self.world.home_at(tile_x, tile_y)),
            getattr(stockpile, "stockpile_type", None),
            bool(workshop),
            (
                getattr(workplace, "workplace_id", None),
                getattr(workplace, "workplace_type", None),
            ) if workplace is not None else None,
            (
                getattr(farm, "origin_x", None),
                getattr(farm, "origin_y", None),
                getattr(farm, "crop_state", None),
                getattr(farm, "growth", None),
                getattr(farm, "food", None),
            ) if farm is not None else None,
        )

    def tile_moisture(self, tile_x: int, tile_y: int) -> float | None:
        moisture_map = getattr(self.world, "moisture_map", None)
        if not moisture_map or tile_y >= len(moisture_map):
            return None
        row = moisture_map[tile_y]
        if tile_x >= len(row):
            return None
        return row[tile_x]

    def terrain_gameplay_state(self, tile_x: int, tile_y: int) -> GameplayVisualState | None:
        farm = self.world.farm_at(tile_x, tile_y)
        settlement = self.world.settlement
        construction_progress = None
        construction_max = None
        if settlement is not None:
            progress = settlement.construction_progress.get((tile_x, tile_y))
            if progress is not None:
                construction_progress = progress
                construction_max = TASK_BUILD_TICKS

        tile = self.world.tile_at(tile_x, tile_y)
        modifiers = tuple(
            modifier
            for modifier in getattr(tile, "visual_modifiers", ())
            if isinstance(modifier, TerrainVisualModifier)
        )
        forest_state = getattr(tile, "forest_state", None)
        building_state = getattr(tile, "building_state", None)
        damage_state = getattr(tile, "damage_state", None)
        biome_state = getattr(tile, "biome_state", None)

        if (
            farm is None
            and construction_progress is None
            and not modifiers
            and forest_state is None
            and building_state is None
            and damage_state is None
            and biome_state is None
        ):
            return None

        return GameplayVisualState(
            crop_state=getattr(farm, "crop_state", None),
            crop_growth=getattr(farm, "growth", 0),
            crop_food=getattr(farm, "food", 0),
            fertility=getattr(farm, "fertility", None),
            construction_progress=construction_progress,
            construction_max=construction_max,
            forest_state=forest_state,
            building_state=building_state,
            damage_state=damage_state,
            biome_state=biome_state,
            modifiers=modifiers,
        )

    def terrain_render_context(self, tile_x: int, tile_y: int) -> TerrainRenderContext:
        return TerrainRenderContext(
            world=self.world,
            tile=self.world.tile_at(tile_x, tile_y),
            tile_x=tile_x,
            tile_y=tile_y,
            grass_state=self.grass_transition_state,
            water_state=self.water_transition_state,
            base_moisture=self.tile_moisture(tile_x, tile_y),
            gameplay_state=self.terrain_gameplay_state(tile_x, tile_y),
            neighbourhood=self.terrain_neighbourhood(tile_x, tile_y),
        )

    def terrain_neighbourhood(self, tile_x: int, tile_y: int):
        return TerrainNeighbourhood.from_world(self.world, tile_x, tile_y)

    def hovered_world_tile(self) -> tuple[int, int] | None:
        if not pygame.mouse.get_focused():
            return None
        return self.screen_to_world_tile(*pygame.mouse.get_pos())

    def inspected_tile(self) -> tuple[int, int] | None:
        if self.selected_tile is not None:
            return self.selected_tile
        return self.hovered_world_tile()

    def draw_agents(self, start_x: int, start_y: int, end_x: int, end_y: int):
        snapshot = self.presentation_scene.snapshot_world(self.world)
        self._agent_tile_counts.clear()
        self._agent_tile_drawn.clear()
        for agent in snapshot.agents:
            key = (agent.tile_x, agent.tile_y)
            self._agent_tile_counts[key] = self._agent_tile_counts.get(key, 0) + 1

        for agent in snapshot.agents:
            render_x, render_y = agent.render_x, agent.render_y
            if not (start_x - 1 <= render_x < end_x + 1 and start_y - 1 <= render_y < end_y + 1):
                continue
            key = (agent.tile_x, agent.tile_y)
            index = self._agent_tile_drawn.get(key, 0)
            self._agent_tile_drawn[key] = index + 1
            offset = VILLAGER_TILE_OFFSETS[index % len(VILLAGER_TILE_OFFSETS)]
            screen_x, screen_y = self.observer_camera.world_to_screen(render_x, render_y, TILE_SIZE)
            self.draw_agent_symbol(agent, screen_x / TILE_SIZE, screen_y / TILE_SIZE, offset)

    def draw_agent_symbol(
        self,
        agent: PresentationAgentSnapshot,
        screen_tile_x: float,
        screen_tile_y: float,
        pixel_offset: tuple[int, int] = (0, 0),
    ):
        self.draw_centered_symbol_at_pixels(
            "@",
            screen_tile_x * TILE_SIZE + TILE_SIZE // 2 + pixel_offset[0],
            screen_tile_y * TILE_SIZE + TILE_SIZE // 2 + pixel_offset[1],
            color_for_role(agent.role),
        )

    def draw_agent_symbol_at_pixels(
        self,
        agent: PresentationAgentSnapshot,
        screen_x: float,
        screen_y: float,
        pixel_offset: tuple[int, int] = (0, 0),
    ):
        self.draw_centered_symbol_at_pixels(
            "@",
            screen_x + TILE_SIZE // 2 + pixel_offset[0],
            screen_y + TILE_SIZE // 2 + pixel_offset[1],
            color_for_role(agent.role),
        )

    def draw_selection_highlight(self):
        if self.selected_agent is not None:
            x = self.selected_agent.x
            y = self.selected_agent.y
            color = COLORS["selection_agent"]
        elif self.selected_tile is not None:
            x, y = self.selected_tile
            color = COLORS["selection"]
        else:
            return

        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        if not (start_x <= x < end_x and start_y <= y < end_y):
            return

        screen_x, screen_y = self.observer_camera.world_to_screen(x, y, TILE_SIZE)

        rect = pygame.Rect(
            round(screen_x),
            round(screen_y),
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.screen, color, rect, 2)

    def draw_centered_symbol(self, symbol: str, x: int, y: int, color: tuple):
        self.draw_centered_symbol_at_pixels(
            symbol,
            x * TILE_SIZE + TILE_SIZE // 2,
            y * TILE_SIZE + TILE_SIZE // 2,
            color,
        )

    def draw_centered_symbol_at_pixels(self, symbol: str, center_x: float, center_y: float, color: tuple):
        surface = self.font.render(symbol, True, color)
        rect = surface.get_rect(center=(round(center_x), round(center_y)))
        self._draw_target.blit(surface, rect)

    def draw_farm_border(self, farm, screen_x: int, screen_y: int, tile_x: int, tile_y: int):
        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        color = COLORS["farm_border"]
        edges = farm_border_edges(farm, tile_x, tile_y)
        if edges["north"]:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.topright, 2)
        if edges["south"]:
            pygame.draw.line(self._draw_target, color, rect.bottomleft, rect.bottomright, 2)
        if edges["west"]:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.bottomleft, 2)
        if edges["east"]:
            pygame.draw.line(self._draw_target, color, rect.topright, rect.bottomright, 2)

    def draw_farm_state_symbol(self, farm, screen_x: int, screen_y: int):
        symbols = {
            FIELD_UNPREPARED: (".", COLORS["muted"]),
            FIELD_PLANTED: (":", COLORS["workplace_farm"]),
            FIELD_GROWING: ('"', COLORS["farm_crop"]),
            FIELD_READY: ("#", COLORS["farm_crop"]),
            FIELD_DORMANT: ("-", COLORS["muted"]),
        }
        symbol, color = symbols.get(farm.crop_state, (".", COLORS["muted"]))
        self.draw_centered_symbol(symbol, screen_x, screen_y, color)

    def draw_path_border(self, screen_x: int, screen_y: int, tile_x: int, tile_y: int):
        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        color = COLORS["path_border"]
        edges = path_border_edges(self.world, tile_x, tile_y)
        if edges["north"]:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.topright, 1)
        if edges["south"]:
            pygame.draw.line(self._draw_target, color, rect.bottomleft, rect.bottomright, 1)
        if edges["west"]:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.bottomleft, 1)
        if edges["east"]:
            pygame.draw.line(self._draw_target, color, rect.topright, rect.bottomright, 1)

    def draw_workplace_placeholder(self, workplace, screen_x: int, screen_y: int, tile_x: int, tile_y: int):
        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        if workplace.workplace_type == FARM:
            color = COLORS["workplace_farm"]
            self.draw_workplace_border(workplace, rect, tile_x, tile_y, color)
            if (tile_x, tile_y) == workplace.position:
                self.draw_centered_symbol(":", screen_x, screen_y, color)
        elif workplace.workplace_type == STORAGE:
            self.draw_workplace_border(workplace, rect, tile_x, tile_y, COLORS["workplace_storage"])
        elif workplace.workplace_type == WORKSHOP:
            self.draw_workplace_border(workplace, rect, tile_x, tile_y, COLORS["workplace_workshop"])
        elif workplace.workplace_type == VILLAGE_CENTER:
            pygame.draw.rect(self._draw_target, COLORS["workplace_center"], rect.inflate(-4, -4), 1)

    def draw_workplace_border(self, workplace, rect, tile_x: int, tile_y: int, color: tuple[int, int, int]):
        tiles = set(workplace.tiles)
        if (tile_x, tile_y - 1) not in tiles:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.topright, 1)
        if (tile_x, tile_y + 1) not in tiles:
            pygame.draw.line(self._draw_target, color, rect.bottomleft, rect.bottomright, 1)
        if (tile_x - 1, tile_y) not in tiles:
            pygame.draw.line(self._draw_target, color, rect.topleft, rect.bottomleft, 1)
        if (tile_x + 1, tile_y) not in tiles:
            pygame.draw.line(self._draw_target, color, rect.topright, rect.bottomright, 1)

    def draw_panel(self, paused: bool, sim_speed: int):
        panel_x = VIEWPORT_WIDTH * TILE_SIZE
        content_x = panel_x + self.panel_padding
        content_width = PANEL_WIDTH - self.panel_padding * 2
        bottom_y = SCREEN_HEIGHT - self.panel_padding

        pygame.draw.rect(
            self.screen,
            COLORS["panel"],
            pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT),
        )

        y = self.panel_padding

        y = self.draw_world_identity_header(content_x, y, content_width, bottom_y)
        y += self.panel_gap

        y = self.draw_time_header(content_x, y, content_width, bottom_y, sim_speed)

        y += self.panel_gap
        y = self.draw_colony_summary(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Active Events", content_x, y, content_width, bottom_y)
        y = self.draw_text_line(
            active_event_names(self.world.active_environment_events),
            content_x,
            y,
            content_width,
            bottom_y,
            color=COLORS["muted"],
        )

        y += self.panel_gap
        y = self.draw_history_summary(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_tile_inspector(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Controls", content_x, y, content_width, bottom_y)
        controls = "WAS/Arrows pan | D diagnostics | V villagers | H history | Space pause | Up/Down speed | R restart | Esc quit"
        y = self.draw_wrapped_text(controls, content_x, y, content_width, bottom_y, COLORS["muted"])

        if self.selected_agent is not None:
            y += self.panel_gap
            y = self.draw_selection_details(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Recent Events", content_x, y, content_width, bottom_y)
        line_height = self.font.get_height() + 3
        max_events = max(0, (bottom_y - y) // line_height)
        if max_events > 0:
            for event in self.world.events[-max_events:]:
                y = self.draw_text_line(event, content_x, y, content_width, bottom_y, color=COLORS["muted"])

    def draw_world_identity_header(self, x: int, y: int, width: int, bottom_y: int):
        identity = self.world.identity
        if identity is None:
            y = self.draw_text_line("Automated Colony", x, y, width, bottom_y, self.big_font)
            return y

        y = self.draw_text_line(identity.title, x, y, width, bottom_y, self.big_font)
        y = self.draw_text_line(identity.subtitle, x, y, width, bottom_y, color=COLORS["muted"])
        y = self.draw_text_line(f"Survival: {identity.survival_outlook}", x, y, width, bottom_y, color=COLORS["warning"])
        return y

    def time_grid_rows(self, sim_speed: int) -> list[tuple[str, object]]:
        return [
            ("Year", self.world.year),
            ("Day", self.world.day),
            ("Speed", f"{sim_speed}x"),
        ]

    def draw_time_grid(self, x: int, y: int, width: int, bottom_y: int, sim_speed: int):
        rows = self.time_grid_rows(sim_speed)
        left_x, column_width, right_x, right_width = self.panel_column_layout(x, width)
        row_y = y
        for index in range(0, len(rows), 2):
            left_label, left_value = rows[index]
            left_bottom = self.draw_compact_stat_row(left_label, left_value, left_x, row_y, column_width, bottom_y)
            right_bottom = row_y
            if index + 1 < len(rows):
                right_label, right_value = rows[index + 1]
                right_bottom = self.draw_compact_stat_row(right_label, right_value, right_x, row_y, right_width, bottom_y)
            row_y = max(left_bottom, right_bottom)
        return row_y

    def draw_time_header(self, x: int, y: int, width: int, bottom_y: int, sim_speed: int):
        y = self.draw_section_header("Time", x, y, width, bottom_y)
        y = self.draw_text_line(f"Season: {self.world.season_label}", x, y, width, bottom_y)
        y = self.draw_day_progress_bar(x, y + 2, width, bottom_y)
        phase_key = village_phase(self.world)
        phase_line = f"{PHASE_ICONS[phase_key]} {settlement_phase_label(self.world)}"
        y = self.draw_text_line(phase_line, x, y + 4, width, bottom_y, color=COLORS["warning"])
        return self.draw_time_grid(x, y, width, bottom_y, sim_speed)

    def draw_day_progress_bar(self, x: int, y: int, width: int, bottom_y: int):
        bar_height = 12
        if y + bar_height > bottom_y:
            return y

        rect = pygame.Rect(x, y, width, bar_height)
        pygame.draw.rect(self.screen, COLORS["grid"], rect)

        inner = rect.inflate(-2, -2)
        for phase, start, end in phase_progress_segments(self.world):
            segment_x = inner.left + round(inner.width * start)
            segment_width = max(1, round(inner.width * (end - start)))
            segment_rect = pygame.Rect(segment_x, inner.top, segment_width, inner.height)
            pygame.draw.rect(self.screen, PHASE_BAR_COLORS[phase], segment_rect)

        marker_x = inner.left + round(inner.width * day_progress(self.world))
        pygame.draw.line(self.screen, COLORS["text"], (marker_x, rect.top - 1), (marker_x, rect.bottom + 1), 2)
        pygame.draw.rect(self.screen, COLORS["muted"], rect, 1)
        return rect.bottom + 3

    def colony_summary_lines(self) -> list[str]:
        settlement = self.world.settlement
        population = len(self.world.living_agents())

        lines = [
            f"Pop      {population}",
        ]
        if settlement is not None:
            lines.append(f"Settlement {settlement.maturity_label}")
            lines.append(f"Age      {settlement.age_years} Years")
            lines.append(f"Homes    {self.home_count()}")
            if settlement.household_count:
                lines.append(f"Households {settlement.household_count}")
                if settlement.average_household_size > 0:
                    lines.append(f"Avg Home {settlement.average_household_size:.1f}")

        lines.extend([
            f"Food     {self.food_status(self.food_target())}",
            f"Water    {self.water_status(self.water_target())}",
            f"Housing  {self.housing_status()}",
        ])
        return lines

    def home_count(self) -> int:
        settlement = self.world.settlement
        if settlement is not None and settlement.homes:
            return len(settlement.homes)
        return self.world.count_tiles("home") + self.world.count_tiles("shelter")

    def food_target(self) -> int:
        return len(self.world.living_agents()) * SETTLEMENT_FOOD_TARGET_DAYS

    def water_target(self) -> int:
        return len(self.world.living_agents()) * SETTLEMENT_WATER_TARGET_DAYS

    def seasonal_food_line(self) -> str:
        settlement = self.world.settlement
        local_food = len(settlement.local_food) if settlement is not None else 0
        return f"Wild Food {local_food} | {self.seasonal_food_status()}"

    def seasonal_food_status(self) -> str:
        if self.world.season == "Winter":
            return "Winter Dormant"
        modifier = SEASON_FOOD_GROWTH_MODIFIERS.get(self.world.season, 1.0)
        if modifier >= 0.9:
            return "Growing"
        if modifier >= 0.25:
            return "Slowing"
        return "Scarce"

    def settlement_priority_lines(self) -> list[str]:
        settlement = self.world.settlement
        if settlement is None:
            return []

        population = len(self.world.living_agents())
        priority = self.world.building_priority()
        housing_structures = self.world.count_tiles("shelter") + self.world.count_tiles("home")
        housing_current = housing_structures * SHELTER_CAPACITY
        housing_target = self.world.needed_houses() * SHELTER_CAPACITY
        wood_target = DESIRED_WOOD_RESERVE + (priority.wood_needed if priority is not None else 0)
        food_target = population * SETTLEMENT_FOOD_TARGET_DAYS
        water_target = population * SETTLEMENT_WATER_TARGET_DAYS

        lines = [
            "Priorities:",
            f"Food     {self.world.colony_storage.food} / {food_target} {self.food_status(food_target)}",
            f"Water    {self.world.colony_storage.water} / {water_target} {self.water_status(water_target)}",
            f"Wood     {self.world.colony_storage.wood} / {wood_target} {self.wood_status(wood_target)}",
            f"Housing  {housing_current} / {housing_target}",
        ]

        if settlement.planned_demands:
            priorities = sorted(settlement.planned_demands.items(), key=lambda item: item[1], reverse=True)
            lines.append("Current Priorities:")
            for index, (name, _) in enumerate(priorities[:3], start=1):
                lines.append(f"{index}. {_planner_label(name)}")
        return lines

    def food_status(self, target: int) -> str:
        population = len(self.world.living_agents())
        carried = sum(agent.food for agent in self.world.living_agents())
        local_food = len(self.world.settlement.local_food) if self.world.settlement is not None else 0
        effective = self.world.colony_storage.food + carried + min(local_food, population)
        if any(agent.hunger >= 70 for agent in self.world.living_agents()) and effective <= population:
            return "Crisis"
        if self.world.colony_storage.food >= target:
            return "Stocked"
        if effective >= max(1, population):
            return "Stable"
        return "Low"

    def water_status(self, target: int) -> str:
        population = len(self.world.living_agents())
        carried = sum(agent.water for agent in self.world.living_agents())
        local_water = len(self.world.settlement.local_water) if self.world.settlement is not None else 0
        effective = self.world.colony_storage.water + carried + min(local_water, population)
        if any(agent.thirst >= 70 for agent in self.world.living_agents()) and effective <= population:
            return "Crisis"
        if self.world.colony_storage.water >= target:
            return "Stocked"
        if effective >= max(1, population):
            return "Stable"
        return "Low"

    def wood_status(self, target: int) -> str:
        priority = self.world.building_priority()
        stored = self.world.colony_storage.wood
        if target > 0 and stored >= target * 2 and priority is None:
            return "Surplus"
        if stored >= target:
            return "Stable"
        if priority is not None:
            return "Needed"
        return "Low"

    def housing_status(self) -> str:
        settlement = self.world.settlement
        if settlement is None:
            return "Unknown"
        report = settlement.carrying_capacity_report
        if report is not None and report.status == "Housing Shortage":
            return "Strained"
        housing_structures = self.world.count_tiles("shelter") + self.world.count_tiles("home")
        housing_current = housing_structures * SHELTER_CAPACITY
        housing_target = self.world.needed_houses() * SHELTER_CAPACITY
        if housing_current >= housing_target:
            return "Stable"
        return "Strained"

    def colony_reason_lines(self, max_lines: int = 3) -> list[str]:
        settlement = self.world.settlement
        if settlement is None or settlement.carrying_capacity_report is None:
            return []
        report = settlement.carrying_capacity_report
        if report.status == "Stable":
            return []

        reasons = []
        population = max(1, report.population)
        if report.status == "Food Strained":
            if self.world.colony_storage.food <= population * 2:
                reasons.append("Food stores low")
            if len(settlement.local_food) <= 2:
                reasons.append("Few local food sources")
            if not any(farm.active for farm in settlement.farm_plots):
                reasons.append("No active farms")
        elif report.status == "Water Strained":
            reasons.append("Limited local water")
        elif report.status == "Housing Shortage":
            reasons.append("Housing capacity short")

        if not reasons:
            reasons.append(report.reason)
        return reasons[:max_lines]

    def draw_colony_summary(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Colony", x, y, width, bottom_y)
        lines = self.colony_summary_lines()
        for index, line in enumerate(lines):
            color = COLORS["warning"] if self.is_colony_warning_line(line) else COLORS["text"]
            if line.startswith(("Settlement", "Age", "Homes", "Households", "Avg Home")):
                color = COLORS["muted"]
            y = self.draw_text_line(line, x, y, width, bottom_y, color=color)
        return y

    def is_colony_warning_line(self, line: str) -> bool:
        return any(
            line.endswith(status)
            for status in ("Crisis", "Low", "Needed", "Strained")
        )

    def draw_tile_inspector(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Tile", x, y, width, bottom_y)
        inspected = self.inspected_tile()
        if inspected is None:
            return self.draw_text_line("Hover over a tile to inspect it.", x, y, width, bottom_y, color=COLORS["muted"])

        tile_x, tile_y = inspected
        rows = self.tile_inspector_rows(tile_x, tile_y)
        for label, value in rows:
            y = self.draw_stat_row(label, value, x, y, width, bottom_y)
        return y

    def tile_inspector_rows(self, tile_x: int, tile_y: int) -> list[tuple[str, object]]:
        tile = self.world.tile_at(tile_x, tile_y)
        context = self.terrain_render_context(tile_x, tile_y)
        visual_state = self.terrain_renderer.visual_state_for(context)
        rows: list[tuple[str, object]] = [
            ("Tile", f"({tile_x}, {tile_y})"),
            ("Terrain", TERRAIN_LABELS.get(tile.kind, tile.kind)),
            ("Season", visual_state.visual_season or visual_state.season),
        ]

        if visual_state.moisture_state is not None:
            rows.append(("Moisture", visual_state.moisture_state))
        if visual_state.weather_state is not None:
            rows.append(("Weather", visual_state.weather_state))
        if visual_state.wear_state is not None:
            rows.append(("Wear", TERRAIN_LABELS.get(visual_state.wear_state, visual_state.wear_state)))
        if tile.foot_traffic > 0:
            rows.append(("Traffic", tile.foot_traffic))

        rows.extend(self.tile_detail_rows(tile_x, tile_y, include_basic=False))
        rows.extend(self.visual_modifier_rows(visual_state.gameplay))
        return rows

    def visual_modifier_rows(self, gameplay: GameplayVisualState | None) -> list[tuple[str, object]]:
        if gameplay is None:
            return []
        rows: list[tuple[str, object]] = []
        if gameplay.crop_state is not None:
            rows.append(("Crop Stage", crop_visual_stage(gameplay.crop_state, gameplay.crop_growth, gameplay.crop_food)))
        if gameplay.construction_progress is not None:
            rows.append(("Construction", construction_visual_stage(gameplay.construction_progress, gameplay.construction_max)))
        if gameplay.forest_state:
            rows.append(("Forest", gameplay.forest_state))
        if gameplay.building_state:
            rows.append(("Building", gameplay.building_state))
        if gameplay.damage_state:
            rows.append(("Damage", gameplay.damage_state))
        if gameplay.biome_state:
            rows.append(("Biome", gameplay.biome_state))
        for modifier in gameplay.modifiers:
            label = modifier.kind.replace("_", " ").title()
            value = modifier.value or f"{modifier.strength:.2f}"
            rows.append((label, value))
        return rows

    def tile_detail_rows(self, tile_x: int, tile_y: int, include_basic: bool = True) -> list[tuple[str, object]]:
        tile = self.world.tile_at(tile_x, tile_y)
        details: list[tuple[str, object]] = []
        if include_basic:
            details.extend([
                ("Tile", f"({tile_x}, {tile_y})"),
                ("Terrain", tile.kind),
            ])
        details.extend([
            ("Food", tile.food if is_food_visible_to_player(self.world, tile_x, tile_y) else "Unknown"),
            ("Wood", tile.wood if is_wood_visible_to_player(self.world, tile_x, tile_y) else "Unknown"),
            ("Walkable", tile.walkable),
        ])

        if self.is_settlement_center(tile_x, tile_y) and self.world.settlement is not None:
            settlement = self.world.settlement
            details.extend([
                ("Settlement", settlement.name),
                ("Maturity", settlement.maturity_label),
                ("Age", f"{settlement.age_years} Years"),
                ("Pop", settlement.population),
                ("Households", settlement.household_count),
                ("Avg HH Size", round(settlement.average_household_size, 1)),
                ("Largest HH", settlement.largest_household_size),
                ("Center", f"{settlement.x},{settlement.y}"),
                ("Radius", settlement.radius),
                ("Founded", f"D{settlement.founded_day} {settlement.founded_season}"),
                ("Claims", len(self.world.reservations.reservations)),
            ])
            report = settlement.carrying_capacity_report
            if report is not None:
                details.extend([
                    ("Capacity", report.capacity),
                    ("Status", report.status),
                ])

        stockpile = self.world.stockpile_at(tile_x, tile_y)
        if stockpile is not None:
            label = "Food" if stockpile.stockpile_type == "food" else "Wood"
            details.extend([
                ("Stockpile", label),
                ("Stored", stockpile.stored_amount),
                ("Capacity", stockpile.capacity),
            ])

        home = self.world.home_at(tile_x, tile_y)
        if home is not None and self.world.settlement is not None:
            household = self.world.settlement.household_for_home(home.home_id)
            details.extend(self.household_detail_rows(home, household))

        workshop = self.world.workshop_at(tile_x, tile_y)
        if workshop is not None:
            details.extend([
                ("Workshop", workshop.kind),
                ("Makes", workshop.production),
                ("Progress", workshop.progress),
                ("Produced", workshop.total_items_produced),
            ])

        workplace = self.world.workplace_at(tile_x, tile_y)
        if workplace is not None:
            details.extend([
                ("Workplace", workplace.workplace_type),
                ("Capacity", workplace.capacity),
                ("Workers", len(workplace.assigned_workers)),
            ])

        farm = self.world.farm_at(tile_x, tile_y)
        if farm is not None:
            details.extend([
                ("Farm Plot", f"{farm.origin_x},{farm.origin_y}"),
                ("Crop State", farm.crop_state),
                ("Growth", farm.growth),
                ("Farm Food", farm.food),
                ("Seed Yield", farm.seed_yield),
                ("Fertility", round(farm.fertility, 2)),
            ])

        return details

    def draw_selection_details(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Selection", x, y, width, bottom_y)

        if self.selected_agent is not None:
            agent = self.selected_agent
            details = compact_villager_rows(agent, self.world)
            details.append(("Details", "Open Villagers overlay"))
            color = COLORS["text"] if agent.alive else COLORS["dead"]

        elif self.selected_tile is not None:
            tile_x, tile_y = self.selected_tile
            details = self.tile_detail_rows(tile_x, tile_y)
            color = COLORS["text"]

        else:
            details = [("Selected", "None")]
            color = COLORS["muted"]

        for label, value in details:
            y = self.draw_stat_row(label, value, x, y, width, bottom_y, color=color)

        return y

    def household_detail_rows(self, home, household) -> list[tuple[str, object]]:
        rows: list[tuple[str, object]] = [("Home", home.home_id or f"{home.x},{home.y}")]
        if household is None:
            return rows

        from src.residential import household_status

        status = household_status(self.world, household)
        rows.extend([
            ("Household", household.household_name),
            ("Household ID", household.household_id),
            ("Founded Year", household.founded_year),
            ("Household Age", household.established_years),
            ("Occupants", f"{status.occupants} / {status.capacity}"),
            ("House Size", f"{status.house_tiles} Tile" if status.house_tiles == 1 else f"{status.house_tiles} Tiles"),
            ("Head", self.household_member_name(household.household_head)),
            ("Members", self.household_member_names(household)),
        ])
        return rows

    def household_member_names(self, household) -> str:
        if household is None or not household.member_ids:
            return "None"
        return ", ".join(self.household_member_name(member_id) for member_id in household.member_ids)

    def household_member_name(self, member_id: str | None) -> str:
        if member_id is None:
            return "None"
        for agent in self.world.agents:
            if (agent.agent_id or agent.name) == member_id:
                return agent.name
        return member_id

    def draw_two_column_section(
        self,
        left_title: str,
        left_rows: list[tuple[str, object]],
        right_title: str,
        right_rows: list[tuple[str, object]],
        x: int,
        y: int,
        width: int,
        bottom_y: int,
    ):
        left_x, column_width, right_x, right_width = self.panel_column_layout(x, width)

        left_y = self.draw_section_header(left_title, left_x, y, column_width, bottom_y)
        right_y = self.draw_section_header(right_title, right_x, y, right_width, bottom_y)
        header_bottom = max(left_y, right_y)

        left_y = header_bottom
        right_y = header_bottom
        for label, value in left_rows:
            left_y = self.draw_compact_stat_row(label, value, left_x, left_y, column_width, bottom_y)
        for label, value in right_rows:
            right_y = self.draw_compact_stat_row(label, value, right_x, right_y, right_width, bottom_y)

        return max(left_y, right_y)

    def panel_column_layout(self, x: int, width: int):
        gap = self.panel_gap * 2
        column_width = (width - gap) // 2
        right_x = x + column_width + gap
        right_width = width - column_width - gap
        return x, column_width, right_x, right_width

    def draw_history_summary(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("History", x, y, width, bottom_y)
        y = self.draw_stat_row("Entries", self.world.history.count(), x, y, width, bottom_y)
        recent = self.world.history.recent(1)
        if recent:
            entry = recent[0]
            y = self.draw_text_line(
                f"Last: D{entry.day} {entry.title}",
                x,
                y,
                width,
                bottom_y,
                color=COLORS["muted"],
            )
        return y

    def tile_color(self, kind: str):
        season_color = seasonal_tile_color(
            kind,
            self.world.season,
            self.world.next_season,
            getattr(self.world, "visual_transition_progress", self.world.transition_progress),
        )
        return season_color

    def is_settlement_center(self, x: int, y: int) -> bool:
        settlement = self.world.settlement
        return settlement is not None and settlement.x == x and settlement.y == y

    def resource_color(self, resource: str, amount: int, cap: int):
        base = COLORS[resource]
        if cap <= 1:
            strength = 1.0
        else:
            strength = max(0.35, min(1.0, amount / cap))

        muted = tuple(max(40, round(channel * 0.45)) for channel in base)
        return tuple(
            round(muted_channel + (base_channel - muted_channel) * strength)
            for muted_channel, base_channel in zip(muted, base)
        )

    def draw_section_header(self, text: str, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_text_line(text, x, y, width, bottom_y, self.big_font)
        return y + 2

    def draw_stat_row(
        self,
        label: str,
        value,
        x: int,
        y: int,
        width: int,
        bottom_y: int,
        color=None,
    ):
        label_text = f"{label}:"
        value_text = str(value)
        line = f"{label_text:<10} {value_text}"
        return self.draw_text_line(line, x, y, width, bottom_y, color=color)

    def draw_compact_stat_row(
        self,
        label: str,
        value,
        x: int,
        y: int,
        width: int,
        bottom_y: int,
        color=None,
    ):
        line = f"{label}: {value}"
        return self.draw_text_line(line, x, y, width, bottom_y, color=color)

    def draw_wrapped_text(self, text: str, x: int, y: int, width: int, bottom_y: int, color=None):
        words = text.split()
        line = ""

        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.font.size(candidate)[0] <= width:
                line = candidate
                continue

            if line:
                y = self.draw_text_line(line, x, y, width, bottom_y, color=color)
            line = word

        if line:
            y = self.draw_text_line(line, x, y, width, bottom_y, color=color)

        return y

    def draw_text_line(self, text: str, x: int, y: int, width: int, bottom_y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        if y + font.get_height() > bottom_y:
            return y

        surface = font.render(self.fit_text(str(text), font, width), True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 3

    def fit_text(self, text: str, font, max_width: int):
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        available_width = max_width - font.size(ellipsis)[0]
        if available_width <= 0:
            return ellipsis

        fitted = ""
        for char in text:
            if font.size(fitted + char)[0] > available_width:
                break
            fitted += char

        return fitted + ellipsis

    def draw_line(self, text: str, x: int, y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 4

    def limit_fps(self):
        self.clock.tick(FPS)
