from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pygame

from src.config import (
    RENDER_DETAIL_HIGH,
    RENDER_DETAIL_LOW,
    RENDER_DETAIL_MEDIUM,
    RENDER_DETAIL_ULTRA,
    TERRAIN_RENDER_DETAIL,
)
from src.environment_events import environmental_tile_color
from src.farming import FIELD_DORMANT, FIELD_GROWING, FIELD_PLANTED, FIELD_READY, FIELD_UNPREPARED
from src.forest_rendering import FOREST_SEASON_PALETTES, FOREST_SEASON_WEIGHTS, forest_visual_season
from src.grass_rendering import (
    DRY,
    GRASS_MOISTURE_PALETTES,
    GRASS_MOISTURE_WEIGHTS,
    NORMAL,
    WET,
    grass_moisture_state,
    grass_visual_moisture_mode,
)
from src.seasons import seasonal_tile_color
from src.renderer_config import RendererArtConfig, load_renderer_art_config
from src.village_paths import DIRT_PATH, PATH, TRAMPLED_GRASS, WORN_GRASS
from src.water_rendering import WATER_WEATHER_PALETTES, WATER_WEATHER_WEIGHTS, water_visual_weather


Color = tuple[int, int, int]
RenderDetail = str
MICROTILE_RESOLUTION_BY_DETAIL: dict[RenderDetail, int] = {
    RENDER_DETAIL_LOW: 1,
    RENDER_DETAIL_MEDIUM: 2,
    RENDER_DETAIL_HIGH: 3,
    RENDER_DETAIL_ULTRA: 5,
}
DEFAULT_RENDER_DETAIL = TERRAIN_RENDER_DETAIL
GRASSLAND_TERRAINS = ("grass", "plain", "hill")
MOISTURE_REACTIVE_TERRAINS = (*GRASSLAND_TERRAINS, TRAMPLED_GRASS, WORN_GRASS, DIRT_PATH, PATH)
PATH_TERRAINS = (TRAMPLED_GRASS, WORN_GRASS, DIRT_PATH, PATH)
NEIGHBOUR_OFFSETS: dict[str, tuple[int, int]] = {
    "nw": (-1, -1),
    "n": (0, -1),
    "ne": (1, -1),
    "w": (-1, 0),
    "e": (1, 0),
    "sw": (-1, 1),
    "s": (0, 1),
    "se": (1, 1),
}
CARDINAL_DIRECTIONS = ("n", "s", "w", "e")
CORNER_DIRECTIONS = ("nw", "ne", "sw", "se")
TERRAIN_TRANSITION_PRIORITY: dict[str, int] = {
    "water": 100,
    PATH: 82,
    DIRT_PATH: 80,
    WORN_GRASS: 78,
    TRAMPLED_GRASS: 76,
    "forest": 70,
    "hill": 54,
    "plain": 48,
    "grass": 44,
    "dry": 42,
    "wetland": 40,
    "mountain": 35,
}
DEFAULT_ART_CONFIG = load_renderer_art_config()
MASTER_VEGETATION_PALETTES: dict[str, tuple[Color, ...]] = DEFAULT_ART_CONFIG.master_vegetation_palettes
VEGETATION_HARMONY_STRENGTH: dict[str, float] = DEFAULT_ART_CONFIG.vegetation_harmony_strength

TERRAIN_PALETTE_ROLES: dict[str, str] = {
    "grass": "grass",
    "plain": "grass",
    "hill": "grass",
    "forest": "forest",
    "wetland": "grass",
}

TERRAIN_MOTIFS: dict[str, tuple[str, ...]] = DEFAULT_ART_CONFIG.terrain_motifs

CALM_INTERIOR_TERRAINS = ("forest", "water", "grass", "plain", "hill")
FOREST_OCCLUSION_RECEIVERS = DEFAULT_ART_CONFIG.ambient_occlusion.forest_receivers

GRASSLAND_PALETTE_FACTORS: dict[str, tuple[float, float, float]] = DEFAULT_ART_CONFIG.terrain_palette_factors

PATH_PALETTES: dict[str, dict[str, tuple[Color, ...]]] = DEFAULT_ART_CONFIG.path_palettes

PATH_WEAR_WEIGHTS: dict[str, tuple[int, ...]] = {
    TRAMPLED_GRASS: (34, 28, 24, 14),
    WORN_GRASS: (30, 30, 24, 16),
    DIRT_PATH: (26, 30, 24, 20),
    PATH: (22, 30, 26, 22),
}

FARM_STAGE_PALETTES: dict[str, tuple[Color, ...]] = {
    "Empty": ((112, 84, 54), (128, 96, 62), (96, 74, 50), (142, 110, 74)),
    "Prepared": ((132, 98, 62), (146, 110, 70), (116, 86, 58), (158, 122, 82)),
    "Planted": ((118, 104, 58), (132, 116, 64), (102, 92, 54), (86, 132, 68)),
    "Sprouting": ((96, 136, 66), (112, 152, 72), (130, 164, 78), (84, 118, 58)),
    "Growing": ((68, 136, 58), (84, 154, 66), (104, 170, 74), (122, 178, 78)),
    "Mature": ((132, 146, 54), (162, 162, 58), (188, 174, 68), (106, 136, 58)),
    "Harvested": ((142, 112, 70), (122, 96, 62), (156, 126, 82), (106, 86, 58)),
    "Fallow": ((116, 104, 82), (132, 118, 92), (98, 92, 76), (146, 132, 104)),
}

CONSTRUCTION_PALETTES: dict[str, tuple[Color, ...]] = {
    "Foundation": ((116, 92, 70), (138, 112, 82), (96, 78, 62), (156, 126, 90)),
    "Under Construction": ((150, 108, 70), (174, 126, 78), (112, 84, 64), (196, 146, 88)),
    "Completed": ((164, 104, 58), (184, 118, 66), (142, 88, 50), (202, 136, 78)),
    "Expanded": ((174, 112, 62), (196, 132, 74), (152, 96, 54), (212, 150, 86)),
    "Damaged": ((100, 84, 76), (122, 96, 82), (82, 72, 68), (144, 110, 88)),
    "Ruined": ((76, 72, 68), (92, 86, 80), (60, 58, 56), (112, 102, 92)),
}

FOREST_LIFECYCLE_PALETTES: dict[str, tuple[Color, ...]] = {
    "Young Forest": ((58, 130, 58), (72, 148, 66), (90, 166, 76), (42, 112, 50)),
    "Mature Forest": FOREST_SEASON_PALETTES["Summer"],
    "Ancient Forest": ((18, 58, 34), (26, 72, 42), (42, 92, 52), (68, 82, 48)),
    "Harvested Forest": ((116, 92, 58), (134, 104, 66), (94, 78, 54), (86, 104, 58)),
    "Recovering Forest": ((74, 124, 62), (92, 142, 70), (110, 154, 78), (62, 104, 58)),
    "Dead Forest": ((82, 74, 64), (100, 90, 76), (64, 60, 56), (118, 106, 88)),
    "Burned Forest": ((42, 38, 34), (58, 52, 44), (76, 68, 56), (28, 28, 28)),
}


@dataclass(frozen=True)
class TerrainVisualModifier:
    kind: str
    value: str | None = None
    strength: float = 1.0


@dataclass(frozen=True)
class GameplayVisualState:
    crop_state: str | None = None
    crop_growth: int = 0
    crop_food: int = 0
    fertility: float | None = None
    construction_progress: int | None = None
    construction_max: int | None = None
    construction_state: str | None = None
    forest_state: str | None = None
    building_state: str | None = None
    damage_state: str | None = None
    biome_state: str | None = None
    modifiers: tuple[TerrainVisualModifier, ...] = ()


@dataclass(frozen=True)
class TerrainVisualState:
    terrain: str
    season: str
    base_color: Color
    visual_season: str | None = None
    moisture_state: str | None = None
    weather_state: str | None = None
    wear_state: str | None = None
    foot_traffic: int = 0
    gameplay: GameplayVisualState | None = None
    environment_tinted: bool = False


@dataclass(frozen=True)
class TerrainRenderContext:
    world: object
    tile: object
    tile_x: int
    tile_y: int
    grass_state: object
    water_state: object
    base_moisture: float | None = None
    gameplay_state: GameplayVisualState | None = None
    neighbourhood: TerrainNeighbourhood | None = None


@dataclass(frozen=True)
class TerrainNeighbourhood:
    """Renderer-only terrain snapshot around one simulation tile."""

    kinds: tuple[tuple[str, str], ...] = ()

    def kind_at(self, direction: str) -> str | None:
        for key, kind in self.kinds:
            if key == direction:
                return kind
        return None

    @classmethod
    def from_world(cls, world: object, tile_x: int, tile_y: int) -> "TerrainNeighbourhood":
        kinds: list[tuple[str, str]] = []
        width = getattr(world, "width", 0)
        height = getattr(world, "height", 0)
        tile_at = getattr(world, "tile_at", None)
        if tile_at is None:
            return cls()
        for direction, (dx, dy) in NEIGHBOUR_OFFSETS.items():
            x = tile_x + dx
            y = tile_y + dy
            if 0 <= x < width and 0 <= y < height:
                kinds.append((direction, getattr(tile_at(x, y), "kind", "plain")))
        return cls(tuple(kinds))


@dataclass(frozen=True)
class MicrotilePattern:
    resolution: int
    colors: tuple[Color, ...]

    @property
    def size(self) -> int:
        return self.resolution * self.resolution


@dataclass(frozen=True)
class MicrotileRect:
    column: int
    row: int
    rect: pygame.Rect


class MicrotileGrid:
    def __init__(self, detail_level: RenderDetail = DEFAULT_RENDER_DETAIL) -> None:
        self.detail_level = detail_level
        self.resolution = microtile_resolution_for_detail(detail_level)

    def rects_for(self, rect: pygame.Rect) -> tuple[MicrotileRect, ...]:
        rects: list[MicrotileRect] = []
        for row in range(self.resolution):
            top = rect.y + (rect.height * row) // self.resolution
            bottom = rect.y + (rect.height * (row + 1)) // self.resolution
            for column in range(self.resolution):
                left = rect.x + (rect.width * column) // self.resolution
                right = rect.x + (rect.width * (column + 1)) // self.resolution
                rects.append(MicrotileRect(column, row, pygame.Rect(left, top, right - left, bottom - top)))
        return tuple(rects)


def microtile_resolution_for_detail(detail_level: RenderDetail) -> int:
    return MICROTILE_RESOLUTION_BY_DETAIL.get(detail_level, MICROTILE_RESOLUTION_BY_DETAIL[RENDER_DETAIL_HIGH])


class TerrainPaletteManager:
    """Central palette source for terrain visuals."""

    def __init__(self, art_config: RendererArtConfig = DEFAULT_ART_CONFIG) -> None:
        self.art_config = art_config
        self._palette_cache: dict[TerrainVisualState, tuple[Color, ...]] = {}
        self._weights_cache: dict[tuple[TerrainVisualState, tuple[Color, ...]], tuple[int, ...]] = {}
        self._neighbour_palette_cache: dict[tuple[str, TerrainVisualState], tuple[Color, ...]] = {}

    def palette_for(self, state: TerrainVisualState) -> tuple[Color, ...]:
        cached = self._palette_cache.get(state)
        if cached is not None:
            return cached

        if state.terrain in GRASSLAND_TERRAINS:
            season_palettes = GRASS_MOISTURE_PALETTES.get(state.visual_season or state.season, GRASS_MOISTURE_PALETTES["Spring"])
            palette = season_palettes.get(state.moisture_state or NORMAL, season_palettes[NORMAL])
            result = self._vegetation_palette(self._terrain_adjusted_palette(palette, state.terrain), state, state.terrain)
        elif state.terrain in PATH_TERRAINS:
            terrain_palettes = PATH_PALETTES.get(state.terrain, PATH_PALETTES[DIRT_PATH])
            result = self._cohesive_earth_palette(terrain_palettes.get(state.moisture_state or NORMAL, terrain_palettes[NORMAL]))
        elif state.terrain == "forest":
            result = self._vegetation_palette(
                FOREST_SEASON_PALETTES.get(state.visual_season or state.season, FOREST_SEASON_PALETTES["Spring"]),
                state,
                "forest",
            )
        elif state.terrain == "water":
            result = self._cohesive_water_palette(WATER_WEATHER_PALETTES.get(state.weather_state or "Clear", WATER_WEATHER_PALETTES["Clear"]))
        elif state.gameplay and state.gameplay.construction_state:
            result = CONSTRUCTION_PALETTES.get(state.gameplay.construction_state, CONSTRUCTION_PALETTES["Under Construction"])
        else:
            result = self._generic_palette(state.base_color)

        self._palette_cache[state] = result
        return result

    def weights_for(self, state: TerrainVisualState, palette: tuple[Color, ...]) -> tuple[int, ...]:
        key = (state, palette)
        cached = self._weights_cache.get(key)
        if cached is not None:
            return cached

        if state.terrain in GRASSLAND_TERRAINS:
            result = self._cohesive_weights(GRASS_MOISTURE_WEIGHTS.get(state.moisture_state or NORMAL, GRASS_MOISTURE_WEIGHTS[NORMAL]), state)
        elif state.terrain in PATH_TERRAINS:
            result = self._cohesive_weights(PATH_WEAR_WEIGHTS.get(state.terrain, PATH_WEAR_WEIGHTS[DIRT_PATH]), state)
        elif state.terrain == "forest":
            result = self._cohesive_weights(FOREST_SEASON_WEIGHTS.get(state.visual_season or state.season, FOREST_SEASON_WEIGHTS["Spring"]), state)
        elif state.terrain == "water":
            result = self._cohesive_weights(WATER_WEATHER_WEIGHTS.get(state.weather_state or "Clear", WATER_WEATHER_WEIGHTS["Clear"]), state)
        elif len(palette) == 4:
            result = (42, 32, 18, 8)
        else:
            result = tuple(1 for _ in palette)

        self._weights_cache[key] = result
        return result

    def palette_for_neighbour(self, terrain: str, state: TerrainVisualState) -> tuple[Color, ...]:
        key = (terrain, state)
        cached = self._neighbour_palette_cache.get(key)
        if cached is not None:
            return cached

        neighbour_state = TerrainVisualState(
            terrain=terrain,
            season=state.season,
            base_color=seasonal_tile_color(terrain, state.season),
            visual_season=state.visual_season,
            moisture_state=state.moisture_state,
            weather_state=state.weather_state,
            wear_state=terrain if terrain in PATH_TERRAINS else None,
            foot_traffic=0,
            gameplay=None,
        )
        result = self.palette_for(neighbour_state)
        self._neighbour_palette_cache[key] = result
        return result

    def _generic_palette(self, base_color: Color) -> tuple[Color, Color, Color, Color]:
        return (
            _shade(base_color, 0.97),
            base_color,
            _shade(base_color, 1.02),
            _shade(base_color, 0.99),
        )

    def _terrain_adjusted_palette(self, palette: tuple[Color, ...], terrain: str) -> tuple[Color, ...]:
        factors = self.art_config.terrain_palette_factors.get(terrain)
        if factors is None:
            return palette
        return tuple(_multiply_color(color, factors) for color in palette)

    def _vegetation_palette(self, palette: tuple[Color, ...], state: TerrainVisualState, terrain: str) -> tuple[Color, ...]:
        master = self.art_config.master_vegetation_palettes.get(
            state.visual_season or state.season,
            self.art_config.master_vegetation_palettes["Spring"],
        )
        strength = self.art_config.vegetation_harmony_strength.get(state.visual_season or state.season, 0.58)
        if terrain == "forest":
            strength *= 0.58
        if state.moisture_state == WET:
            palette = tuple(_mix_color(color, (52, 108, 64), 0.12) for color in palette)
        elif state.moisture_state == DRY:
            palette = tuple(_mix_color(color, (136, 126, 78), 0.14) for color in palette)
        return tuple(_mix_color(color, master[index % len(master)], strength) for index, color in enumerate(palette))

    def _cohesive_earth_palette(self, palette: tuple[Color, ...]) -> tuple[Color, ...]:
        anchor = _average_color(palette)
        return tuple(_mix_color(color, anchor, 0.28) for color in palette)

    def _cohesive_water_palette(self, palette: tuple[Color, ...]) -> tuple[Color, ...]:
        anchor = _average_color(palette)
        return tuple(_mix_color(color, anchor, 0.18) for color in palette)

    def _cohesive_weights(self, weights: tuple[int, ...], state: TerrainVisualState) -> tuple[int, ...]:
        if not weights:
            return weights
        if (state.visual_season or state.season) == "Autumn":
            return weights
        softened = list(weights)
        softened[0] += max(4, sum(weights) // 8)
        if len(softened) > 3:
            softened[-1] = max(1, softened[-1] // 2)
        return tuple(softened)


class TerrainModifierStack:
    """Composable visual modifiers applied after base environmental palettes."""

    def apply(self, palette: tuple[Color, ...], state: TerrainVisualState) -> tuple[Color, ...]:
        gameplay = state.gameplay
        if gameplay is None:
            return palette

        result = palette
        if gameplay.biome_state:
            result = self._apply_biome(result, gameplay.biome_state)
        if gameplay.forest_state:
            result = self._blend_with_palette(result, FOREST_LIFECYCLE_PALETTES.get(gameplay.forest_state), 0.75)
        if gameplay.crop_state:
            crop_stage = crop_visual_stage(gameplay.crop_state, gameplay.crop_growth, gameplay.crop_food)
            result = self._blend_with_palette(result, farm_stage_palette(crop_stage, state.visual_season or state.season), 0.82)
        if gameplay.construction_progress is not None or gameplay.construction_state:
            stage = gameplay.construction_state or construction_visual_stage(gameplay.construction_progress or 0, gameplay.construction_max)
            result = self._blend_with_palette(result, CONSTRUCTION_PALETTES.get(stage), 0.9)
        if gameplay.building_state:
            result = self._apply_building_state(result, gameplay.building_state)
        if gameplay.damage_state:
            result = self._apply_damage(result, gameplay.damage_state)

        for modifier in gameplay.modifiers:
            result = self.apply_modifier(result, modifier)
        return result

    def apply_modifier(self, palette: tuple[Color, ...], modifier: TerrainVisualModifier) -> tuple[Color, ...]:
        strength = max(0.0, min(1.0, modifier.strength))
        if modifier.kind == "snow":
            targets = {
                "Light Snow": (214, 224, 220),
                "Medium Snow": (226, 234, 232),
                "Deep Snow": (238, 244, 244),
                "Melting Snow": (184, 204, 198),
            }
            return _mix_palette_with_color(palette, targets.get(modifier.value or "", (226, 234, 232)), 0.45 * strength)
        if modifier.kind in ("burnt", "fire"):
            targets = {
                "Burning": (188, 86, 34),
                "Charred": (44, 38, 34),
                "Ash": (96, 92, 88),
                "Regrowth": (82, 124, 64),
            }
            return _mix_palette_with_color(palette, targets.get(modifier.value or "", (56, 50, 44)), 0.65 * strength)
        if modifier.kind == "flood":
            targets = {
                "Water Expansion": (58, 102, 144),
                "Wet Shoreline": (84, 96, 82),
                "Floodplain": (74, 112, 104),
                "Mud": (82, 62, 48),
            }
            return _mix_palette_with_color(palette, targets.get(modifier.value or "", (74, 104, 118)), 0.55 * strength)
        if modifier.kind == "magic":
            targets = {
                "Blessed": (184, 178, 96),
                "Corrupted": (86, 46, 104),
                "Enchanted": (72, 138, 154),
                "Cursed": (66, 48, 82),
                "Mystical": (118, 82, 164),
            }
            return _mix_palette_with_color(palette, targets.get(modifier.value or "", (118, 82, 164)), 0.5 * strength)
        if modifier.kind == "damage":
            return _mix_palette_with_color(palette, (68, 62, 58), 0.45 * strength)
        return palette

    def _apply_biome(self, palette: tuple[Color, ...], biome: str) -> tuple[Color, ...]:
        factors = {
            "Temperate": (1.0, 1.0, 1.0),
            "Boreal": (0.82, 0.96, 1.02),
            "Grassland": (1.12, 1.08, 0.84),
            "Wetland": (0.82, 1.02, 1.02),
            "Highland": (1.0, 0.96, 0.88),
            "Ancient Forest": (0.72, 0.88, 0.76),
        }.get(biome)
        if factors is None:
            return palette
        return tuple(_multiply_color(color, factors) for color in palette)

    def _apply_building_state(self, palette: tuple[Color, ...], building_state: str) -> tuple[Color, ...]:
        return self._blend_with_palette(palette, CONSTRUCTION_PALETTES.get(building_state), 0.8)

    def _apply_damage(self, palette: tuple[Color, ...], damage_state: str) -> tuple[Color, ...]:
        strength = {
            "Damaged": 0.35,
            "Ruined": 0.65,
        }.get(damage_state, 0.4)
        return _mix_palette_with_color(palette, (72, 66, 60), strength)

    def _blend_with_palette(self, palette: tuple[Color, ...], target: tuple[Color, ...] | None, strength: float) -> tuple[Color, ...]:
        if target is None:
            return palette
        return tuple(_mix_color(color, target[index % len(target)], strength) for index, color in enumerate(palette))


class TerrainPatternGenerator:
    """Shared deterministic microtile pattern generator."""

    def __init__(self, art_config: RendererArtConfig = DEFAULT_ART_CONFIG) -> None:
        self.art_config = art_config
        self._pattern_cache: dict[
            tuple[int | None, int, int, TerrainVisualState, tuple[Color, ...], tuple[int, ...], RenderDetail],
            MicrotilePattern,
        ] = {}

    def generate_pattern(
        self,
        seed: int | None,
        tile_x: int,
        tile_y: int,
        state: TerrainVisualState,
        palette: tuple[Color, ...],
        weights: tuple[int, ...],
        detail_level: RenderDetail = DEFAULT_RENDER_DETAIL,
    ) -> MicrotilePattern:
        key = (seed, tile_x, tile_y, state, palette, weights, detail_level)
        cached = self._pattern_cache.get(key)
        if cached is not None:
            return cached

        resolution = microtile_resolution_for_detail(detail_level)
        colors: list[Color] = []
        identity = self._state_identity(state)
        motif = self._motif_for(seed, tile_x, tile_y, state, identity)
        for microtile in range(resolution * resolution):
            row, column = divmod(microtile, resolution)
            cluster_row, cluster_column = self._cluster_for(row, column, resolution, motif)
            cluster_roll = _stable_int(
                seed,
                tile_x,
                tile_y,
                state.terrain,
                identity,
                detail_level,
                resolution,
                motif,
                cluster_row,
                cluster_column,
            )
            motif_weights = self._motif_weights(state, motif, weights)
            color = _weighted_color(palette, motif_weights, cluster_roll)
            if self._should_add_accent(seed, tile_x, tile_y, state, motif, row, column, resolution):
                accent_roll = _stable_int(seed, tile_x, tile_y, state.terrain, identity, motif, row, column, "accent")
                color = _mix_color(color, palette[accent_roll % len(palette)], 0.35)
            colors.append(color)
        if len(set(colors)) == 1 and len(palette) > 1:
            replacement_index = _stable_int(seed, tile_x, tile_y, state.terrain, identity, detail_level, resolution, motif, "variation") % len(palette)
            replacement = palette[replacement_index]
            if replacement == colors[0]:
                replacement = palette[(replacement_index + 1) % len(palette)]
            colors[-1] = _mix_color(colors[-1], replacement, 0.42)
        pattern = MicrotilePattern(resolution=resolution, colors=tuple(colors))
        self._pattern_cache[key] = pattern
        return pattern

    def _motif_for(self, seed: int | None, tile_x: int, tile_y: int, state: TerrainVisualState, identity: tuple[object, ...]) -> str:
        motifs = self.art_config.terrain_motifs.get(state.terrain, ("soft_patch", "open_patch", "quiet_patch"))
        index = _stable_int(seed, tile_x, tile_y, state.terrain, identity, "motif") % len(motifs)
        return motifs[index]

    def _cluster_for(self, row: int, column: int, resolution: int, motif: str) -> tuple[int, int]:
        if resolution <= 2:
            return row, column
        cluster_size = 3 if resolution >= 5 and motif in ("dense_canopy", "calm_surface", "meadow", "open_sward") else 2
        return row // cluster_size, column // cluster_size

    def _motif_weights(self, state: TerrainVisualState, motif: str, weights: tuple[int, ...]) -> tuple[int, ...]:
        adjusted = list(weights)
        if not adjusted:
            return weights
        if motif in ("dense_canopy", "canopy_mass", "calm_surface", "meadow", "open_sward", "compacted_earth", "packed_track"):
            adjusted[0] += max(6, sum(adjusted) // 5)
            if len(adjusted) > 3:
                adjusted[-1] = max(1, adjusted[-1] // 3)
        elif motif in ("small_clearing", "flowering_patch", "wheel_rut", "rain_disturbance"):
            if len(adjusted) > 2:
                adjusted[2] += max(3, sum(adjusted) // 10)
            if len(adjusted) > 3 and (state.visual_season or state.season) != "Autumn":
                adjusted[-1] = max(1, adjusted[-1] // 2)
        elif motif in ("worn_patch", "dusty_patch", "worn_shoulder", "dry_meadow"):
            if len(adjusted) > 1:
                adjusted[1] += max(4, sum(adjusted) // 8)
        return tuple(adjusted)

    def _should_add_accent(
        self,
        seed: int | None,
        tile_x: int,
        tile_y: int,
        state: TerrainVisualState,
        motif: str,
        row: int,
        column: int,
        resolution: int,
    ) -> bool:
        if resolution <= 2:
            return False
        season = state.visual_season or state.season
        chance = 7
        if season == "Autumn":
            chance = 18
        elif state.terrain in CALM_INTERIOR_TERRAINS:
            chance = 5
        if motif in ("small_clearing", "flowering_patch", "wheel_rut", "rain_disturbance", "ripple_cluster"):
            chance += 6
        roll = _stable_int(seed, tile_x, tile_y, state.terrain, motif, row, column, resolution, "accent")
        return roll % 100 < chance

    def _state_identity(self, state: TerrainVisualState) -> tuple[object, ...]:
        return (
            state.season,
            state.visual_season,
            state.moisture_state,
            state.weather_state,
            state.wear_state,
            state.gameplay,
            state.base_color,
        )


@dataclass(frozen=True)
class EdgeMask:
    direction: str
    neighbour_terrain: str


class TerrainEdgeShaper:
    """Applies deterministic edge ownership masks to microtile patterns."""

    def __init__(self, palette_manager: TerrainPaletteManager, art_config: RendererArtConfig = DEFAULT_ART_CONFIG) -> None:
        self.palette_manager = palette_manager
        self.art_config = art_config
        self._edge_mask_cache: dict[tuple[str, tuple[tuple[str, str], ...], bool], tuple[EdgeMask, ...]] = {}

    def apply(self, pattern: MicrotilePattern, state: TerrainVisualState, context: TerrainRenderContext) -> MicrotilePattern:
        neighbourhood = context.neighbourhood
        if neighbourhood is None or pattern.resolution <= 1:
            return pattern

        colors = list(pattern.colors)
        masks = self.edge_masks_for(state, neighbourhood)
        for mask in masks:
            neighbour_palette = self.palette_manager.palette_for_neighbour(mask.neighbour_terrain, state)
            for index, row, column in self._indices_for(mask.direction, pattern.resolution):
                if self._neighbour_owns_edge(context, state, mask, row, column, pattern.resolution):
                    colors[index] = self._edge_color(neighbour_palette, context, state, mask, row, column)
        return MicrotilePattern(resolution=pattern.resolution, colors=tuple(colors))

    def edge_masks_for(self, state: TerrainVisualState, neighbourhood: TerrainNeighbourhood) -> tuple[EdgeMask, ...]:
        key = (
            state.terrain,
            neighbourhood.kinds,
            self.art_config.path_visual_language.edge_shaping_enabled,
        )
        cached = self._edge_mask_cache.get(key)
        if cached is not None:
            return cached

        masks: list[EdgeMask] = []
        for direction in CARDINAL_DIRECTIONS + CORNER_DIRECTIONS:
            neighbour = neighbourhood.kind_at(direction)
            if neighbour is None or not self._should_shape(state.terrain, neighbour):
                continue
            masks.append(EdgeMask(direction, neighbour))
        result = tuple(masks)
        self._edge_mask_cache[key] = result
        return result

    def _should_shape(self, terrain: str, neighbour: str) -> bool:
        if terrain == neighbour:
            return False
        if (terrain in PATH_TERRAINS or neighbour in PATH_TERRAINS) and not self.art_config.path_visual_language.edge_shaping_enabled:
            return False
        if terrain in PATH_TERRAINS or neighbour in PATH_TERRAINS:
            return True
        if terrain == "water" or neighbour == "water":
            return True
        if terrain == "forest" or neighbour == "forest":
            return True
        if terrain in GRASSLAND_TERRAINS and neighbour in GRASSLAND_TERRAINS:
            return True
        return self._priority(neighbour) > self._priority(terrain)

    def _priority(self, terrain: str) -> int:
        return TERRAIN_TRANSITION_PRIORITY.get(terrain, 45)

    def _neighbour_owns_edge(
        self,
        context: TerrainRenderContext,
        state: TerrainVisualState,
        mask: EdgeMask,
        row: int,
        column: int,
        resolution: int,
    ) -> bool:
        priority_delta = self._priority(mask.neighbour_terrain) - self._priority(state.terrain)
        base_chance = 18
        if priority_delta > 0:
            base_chance += min(28, priority_delta // 2)
        elif priority_delta < 0:
            base_chance -= min(10, abs(priority_delta) // 4)
        if state.terrain in PATH_TERRAINS:
            base_chance = min(base_chance, 18)
        if mask.neighbour_terrain in PATH_TERRAINS:
            base_chance += 10
        if state.terrain == "water":
            base_chance = min(base_chance, 16)
        if mask.neighbour_terrain == "water":
            base_chance += 14
        if mask.direction in CORNER_DIRECTIONS:
            base_chance -= 8
        if resolution <= 2:
            base_chance = min(base_chance, 18)
        base_chance = max(4, min(54, base_chance))
        roll = _stable_int(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state.terrain,
            mask.direction,
            mask.neighbour_terrain,
            row // 2,
            column // 2,
            resolution,
            "edge-owner",
        )
        return roll % 100 < base_chance

    def _indices_for(self, direction: str, resolution: int):
        for row in range(resolution):
            for column in range(resolution):
                if self._matches(direction, row, column, resolution):
                    yield row * resolution + column, row, column

    def _matches(self, direction: str, row: int, column: int, resolution: int) -> bool:
        last = resolution - 1
        return (
            direction == "n" and row == 0
            or direction == "s" and row == last
            or direction == "w" and column == 0
            or direction == "e" and column == last
            or direction == "nw" and row == 0 and column == 0
            or direction == "ne" and row == 0 and column == last
            or direction == "sw" and row == last and column == 0
            or direction == "se" and row == last and column == last
        )

    def _edge_color(
        self,
        palette: tuple[Color, ...],
        context: TerrainRenderContext,
        state: TerrainVisualState,
        mask: EdgeMask,
        row: int,
        column: int,
    ) -> Color:
        roll = _stable_int(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state.terrain,
            mask.direction,
            mask.neighbour_terrain,
            self._priority(mask.neighbour_terrain),
            row // 2,
            column // 2,
            "edge",
        )
        return palette[roll % len(palette)]


class AmbientTerrainOcclusion:
    """Subtle renderer-only ambient influence from nearby terrain."""

    def __init__(self, art_config: RendererArtConfig = DEFAULT_ART_CONFIG) -> None:
        self.art_config = art_config

    def apply(self, pattern: MicrotilePattern, state: TerrainVisualState, context: TerrainRenderContext) -> MicrotilePattern:
        neighbourhood = context.neighbourhood
        if neighbourhood is None or pattern.resolution <= 1:
            return pattern
        if not self._can_receive_occlusion(state, context):
            return pattern

        forest_directions = tuple(
            direction
            for direction in CARDINAL_DIRECTIONS + CORNER_DIRECTIONS
            if neighbourhood.kind_at(direction) == "forest"
        )
        if not forest_directions:
            return pattern

        density = self._forest_density(neighbourhood)
        colors = list(pattern.colors)
        for direction in forest_directions:
            for index, row, column, distance in self._influence_indices(direction, pattern.resolution, density):
                if self._should_apply(context, state, direction, row, column, distance, density):
                    colors[index] = self._shade_receiver(colors[index], distance, density)
        return MicrotilePattern(resolution=pattern.resolution, colors=tuple(colors))

    def _can_receive_occlusion(self, state: TerrainVisualState, context: TerrainRenderContext) -> bool:
        if state.terrain not in self.art_config.ambient_occlusion.forest_receivers:
            return False
        if state.terrain in PATH_TERRAINS or state.terrain in ("water", "forest", "mountain", "hill"):
            return False
        gameplay = state.gameplay
        if gameplay and (
            gameplay.crop_state
            or gameplay.construction_progress is not None
            or gameplay.construction_state
            or gameplay.building_state
        ):
            return False

        world = context.world
        for accessor_name in ("home_at", "farm_at", "workplace_at", "stockpile_at", "workshop_at"):
            accessor = getattr(world, accessor_name, None)
            if accessor is not None and accessor(context.tile_x, context.tile_y):
                return False
        return True

    def _forest_density(self, neighbourhood: TerrainNeighbourhood) -> int:
        return sum(1 for _, kind in neighbourhood.kinds if kind == "forest")

    def _influence_indices(self, direction: str, resolution: int, density: int):
        max_distance = 2 if resolution >= 5 and density >= 4 else 1
        for row in range(resolution):
            for column in range(resolution):
                distance = self._distance_from_direction(direction, row, column, resolution)
                if 1 <= distance <= max_distance:
                    yield row * resolution + column, row, column, distance

    def _distance_from_direction(self, direction: str, row: int, column: int, resolution: int) -> int:
        last = resolution - 1
        distances = []
        if "n" in direction:
            distances.append(row + 1)
        if "s" in direction:
            distances.append(last - row + 1)
        if "w" in direction:
            distances.append(column + 1)
        if "e" in direction:
            distances.append(last - column + 1)
        return max(distances) if direction in CORNER_DIRECTIONS else min(distances)

    def _should_apply(
        self,
        context: TerrainRenderContext,
        state: TerrainVisualState,
        direction: str,
        row: int,
        column: int,
        distance: int,
        density: int,
    ) -> bool:
        config = self.art_config.ambient_occlusion
        chance = config.first_microtile_chance if distance == 1 else config.second_microtile_chance
        chance += min(config.max_chance_bonus, max(0, density - 1) * config.density_chance_bonus)
        roll = _stable_int(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state.terrain,
            direction,
            row,
            column,
            distance,
            density,
            "ambient-occlusion",
        )
        return roll % 100 < min(92, chance)

    def _shade_receiver(self, color: Color, distance: int, density: int) -> Color:
        config = self.art_config.ambient_occlusion
        darken = config.first_microtile_darken if distance == 1 else config.second_microtile_darken
        darken += min(config.max_density_bonus, max(0, density - 2) * config.density_bonus)
        return _shade(color, 1.0 - darken)


class PathForestEncroachment:
    """Subtle deterministic leaf/grass flecks on forest-adjacent paths."""

    def __init__(self, art_config: RendererArtConfig = DEFAULT_ART_CONFIG) -> None:
        self.art_config = art_config

    def apply(self, pattern: MicrotilePattern, state: TerrainVisualState, context: TerrainRenderContext) -> MicrotilePattern:
        config = self.art_config.path_visual_language
        neighbourhood = context.neighbourhood
        if not config.encroachment_enabled or neighbourhood is None or pattern.resolution <= 1:
            return pattern
        if state.terrain not in config.encroachment_terrains:
            return pattern

        forest_directions = tuple(
            direction
            for direction in CARDINAL_DIRECTIONS + CORNER_DIRECTIONS
            if neighbourhood.kind_at(direction) == "forest"
        )
        if not forest_directions:
            return pattern

        seasonal_palette = self.art_config.master_vegetation_palettes.get(
            state.visual_season or state.season,
            self.art_config.master_vegetation_palettes["Spring"],
        )
        colors = list(pattern.colors)
        for direction in forest_directions:
            for index, row, column in self._edge_indices(direction, pattern.resolution):
                if self._should_encroach(context, state, direction, row, column):
                    roll = _stable_int(
                        getattr(context.world, "seed", None),
                        context.tile_x,
                        context.tile_y,
                        state.terrain,
                        direction,
                        row,
                        column,
                        "path-forest-encroachment-color",
                    )
                    colors[index] = _mix_color(colors[index], seasonal_palette[roll % len(seasonal_palette)], config.forest_encroachment_strength)
        return MicrotilePattern(resolution=pattern.resolution, colors=tuple(colors))

    def _edge_indices(self, direction: str, resolution: int):
        last = resolution - 1
        for row in range(resolution):
            for column in range(resolution):
                if (
                    "n" in direction and row == 0
                    or "s" in direction and row == last
                    or "w" in direction and column == 0
                    or "e" in direction and column == last
                ):
                    yield row * resolution + column, row, column

    def _should_encroach(self, context: TerrainRenderContext, state: TerrainVisualState, direction: str, row: int, column: int) -> bool:
        roll = _stable_int(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state.terrain,
            direction,
            row,
            column,
            "path-forest-encroachment",
        )
        return roll % 100 < self.art_config.path_visual_language.forest_encroachment_chance


class TerrainRenderer:
    """Shared terrain rendering pipeline for every map tile."""

    def __init__(
        self,
        palette_manager: TerrainPaletteManager | None = None,
        pattern_generator: TerrainPatternGenerator | None = None,
        modifier_stack: TerrainModifierStack | None = None,
        detail_level: RenderDetail = DEFAULT_RENDER_DETAIL,
    ) -> None:
        self.palette_manager = palette_manager or TerrainPaletteManager()
        self.pattern_generator = pattern_generator or TerrainPatternGenerator()
        self.modifier_stack = modifier_stack or TerrainModifierStack()
        self.art_config = self.palette_manager.art_config
        self.edge_shaper = TerrainEdgeShaper(self.palette_manager, self.art_config)
        self.ambient_occlusion = AmbientTerrainOcclusion(self.art_config)
        self.path_encroachment = PathForestEncroachment(self.art_config)
        self.detail_level = detail_level
        self.microtile_grid = MicrotileGrid(detail_level)
        self._microtile_pattern_cache: dict[tuple[object, ...], MicrotilePattern] = {}

    def set_detail_level(self, detail_level: RenderDetail) -> None:
        self.detail_level = detail_level
        self.microtile_grid = MicrotileGrid(detail_level)
        self._microtile_pattern_cache.clear()

    def visual_state_for(self, context: TerrainRenderContext) -> TerrainVisualState:
        world = context.world
        tile = context.tile
        terrain = getattr(tile, "kind", "plain")
        season = getattr(world, "season", "Spring")
        base_color = seasonal_tile_color(
            terrain,
            season,
            getattr(world, "next_season", None),
            getattr(world, "transition_progress", 0.0),
        )
        events = getattr(world, "active_environment_events", ())

        if terrain in MOISTURE_REACTIVE_TERRAINS:
            visual_mode = grass_visual_moisture_mode(
                getattr(world, "seed", None),
                context.tile_x,
                context.tile_y,
                context.grass_state,
                getattr(world, "tick", 0),
            )
            visual_season = season
            if terrain in GRASSLAND_TERRAINS and getattr(world, "day", 1) > 1:
                visual_season = forest_visual_season(
                    getattr(world, "seed", None),
                    context.tile_x,
                    context.tile_y,
                    season,
                    getattr(world, "day_of_season", 1),
                )
            return TerrainVisualState(
                terrain=terrain,
                season=season,
                base_color=base_color,
                visual_season=visual_season,
                moisture_state=grass_moisture_state(context.base_moisture, visual_mode),
                wear_state=terrain if terrain in PATH_TERRAINS else None,
                foot_traffic=getattr(tile, "foot_traffic", 0),
                gameplay=context.gameplay_state,
            )
        if terrain == "forest":
            return TerrainVisualState(
                terrain=terrain,
                season=season,
                base_color=base_color,
                visual_season=forest_visual_season(
                    getattr(world, "seed", None),
                    context.tile_x,
                    context.tile_y,
                    season,
                    getattr(world, "day_of_season", 1),
                ),
                gameplay=context.gameplay_state,
                environment_tinted=bool(events),
            )
        if terrain == "water":
            return TerrainVisualState(
                terrain=terrain,
                season=season,
                base_color=base_color,
                weather_state=water_visual_weather(
                    getattr(world, "seed", None),
                    context.tile_x,
                    context.tile_y,
                    context.water_state,
                    getattr(world, "tick", 0),
                ),
                gameplay=context.gameplay_state,
            )
        return TerrainVisualState(
            terrain=terrain,
            season=season,
            base_color=environmental_tile_color(base_color, terrain, events),
            gameplay=context.gameplay_state,
        )

    def microtile_pattern_for(self, context: TerrainRenderContext) -> MicrotilePattern:
        state = self.visual_state_for(context)
        cache_key = self.microtile_cache_key(context, state)
        cached = self._microtile_pattern_cache.get(cache_key)
        if cached is not None:
            return cached

        palette = self.palette_manager.palette_for(state)
        palette = self.modifier_stack.apply(palette, state)
        weights = self.palette_manager.weights_for(state, palette)
        pattern = self.pattern_generator.generate_pattern(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state,
            palette,
            weights,
            self.detail_level,
        )
        pattern = self.ambient_occlusion.apply(pattern, state, context)
        pattern = self.edge_shaper.apply(pattern, state, context)
        pattern = self.path_encroachment.apply(pattern, state, context)
        if state.environment_tinted:
            events = getattr(context.world, "active_environment_events", ())
            pattern = MicrotilePattern(
                resolution=pattern.resolution,
                colors=tuple(environmental_tile_color(color, state.terrain, events) for color in pattern.colors),
            )
        self._microtile_pattern_cache[cache_key] = pattern
        return pattern

    def microtile_cache_key(self, context: TerrainRenderContext, state: TerrainVisualState) -> tuple[object, ...]:
        return (
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            self.detail_level,
            state,
            context.neighbourhood.kinds if context.neighbourhood is not None else (),
            tuple(
                sorted(
                    (
                        getattr(event, "effect_type", None),
                        getattr(event, "remaining_days", None),
                    )
                    for event in getattr(context.world, "active_environment_events", ())
                )
            ),
        )

    def microtile_colors_for(self, context: TerrainRenderContext) -> tuple[Color, ...]:
        return self.microtile_pattern_for(context).colors

    def draw_tile(self, surface: pygame.Surface, rect: pygame.Rect, context: TerrainRenderContext) -> None:
        pattern = self.microtile_pattern_for(context)
        for microtile, color in zip(self.microtile_grid.rects_for(rect), pattern.colors):
            pygame.draw.rect(surface, color, microtile.rect)


def _shade(color: Color, factor: float) -> Color:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)  # type: ignore[return-value]


def _multiply_color(color: Color, factors: tuple[float, float, float]) -> Color:
    return tuple(max(0, min(255, int(channel * factor))) for channel, factor in zip(color, factors))  # type: ignore[return-value]


def _mix_color(color: Color, target: Color, strength: float) -> Color:
    strength = max(0.0, min(1.0, strength))
    return tuple(round(channel + (target_channel - channel) * strength) for channel, target_channel in zip(color, target))  # type: ignore[return-value]


def _average_color(palette: tuple[Color, ...]) -> Color:
    if not palette:
        return (0, 0, 0)
    count = len(palette)
    return (
        round(sum(color[0] for color in palette) / count),
        round(sum(color[1] for color in palette) / count),
        round(sum(color[2] for color in palette) / count),
    )


def palette_spread(palette: tuple[Color, ...]) -> int:
    if len(palette) < 2:
        return 0
    return max(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        for index, a in enumerate(palette)
        for b in palette[index + 1 :]
    )


def _mix_palette_with_color(palette: tuple[Color, ...], target: Color, strength: float) -> tuple[Color, ...]:
    return tuple(_mix_color(color, target, strength) for color in palette)


def farm_stage_palette(stage: str, season: str) -> tuple[Color, ...]:
    palette = FARM_STAGE_PALETTES.get(stage, FARM_STAGE_PALETTES["Empty"])
    if stage in ("Planted", "Sprouting", "Growing", "Mature"):
        master = MASTER_VEGETATION_PALETTES.get(season, MASTER_VEGETATION_PALETTES["Spring"])
        strength = 0.42 if season != "Autumn" else 0.24
        return tuple(_mix_color(color, master[index % len(master)], strength) for index, color in enumerate(palette))
    return tuple(_mix_color(color, _average_color(palette), 0.18) for color in palette)


def crop_visual_stage(crop_state: str, growth: int = 0, food: int = 0) -> str:
    if crop_state == FIELD_UNPREPARED:
        return "Harvested" if food <= 0 and growth <= 0 else "Prepared"
    if crop_state == FIELD_PLANTED:
        return "Sprouting" if growth > 0 else "Planted"
    if crop_state == FIELD_GROWING:
        return "Growing"
    if crop_state == FIELD_READY:
        return "Mature"
    if crop_state == FIELD_DORMANT:
        return "Fallow"
    return crop_state


def construction_visual_stage(progress: int, maximum: int | None = None) -> str:
    if maximum is None or maximum <= 0:
        maximum = 1
    ratio = max(0.0, min(1.0, progress / maximum))
    if ratio <= 0.2:
        return "Foundation"
    if ratio < 1.0:
        return "Under Construction"
    return "Completed"


def _weighted_color(palette: tuple[Color, ...], weights: tuple[int, ...], roll: int) -> Color:
    total = max(1, sum(weights))
    marker = roll % total
    running = 0
    for color, weight in zip(palette, weights):
        running += weight
        if marker < running:
            return color
    return palette[-1]


def _stable_int(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")
