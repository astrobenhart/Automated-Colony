from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pygame

from src.config import TILE_SIZE
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
from src.village_paths import DIRT_PATH, PATH, TRAMPLED_GRASS, WORN_GRASS
from src.water_rendering import WATER_WEATHER_PALETTES, WATER_WEATHER_WEIGHTS, water_visual_weather


Color = tuple[int, int, int]
GRASSLAND_TERRAINS = ("grass", "plain", "hill")
MOISTURE_REACTIVE_TERRAINS = (*GRASSLAND_TERRAINS, TRAMPLED_GRASS, WORN_GRASS, DIRT_PATH, PATH)
PATH_TERRAINS = (TRAMPLED_GRASS, WORN_GRASS, DIRT_PATH, PATH)

GRASSLAND_PALETTE_FACTORS: dict[str, tuple[float, float, float]] = {
    "grass": (1.0, 1.0, 1.0),
    "plain": (1.08, 1.05, 0.88),
    "hill": (1.10, 1.00, 0.82),
}

PATH_PALETTES: dict[str, dict[str, tuple[Color, ...]]] = {
    TRAMPLED_GRASS: {
        DRY: ((138, 128, 82), (150, 136, 92), (116, 112, 78), (160, 148, 104)),
        NORMAL: ((118, 112, 74), (130, 120, 82), (104, 104, 72), (142, 132, 92)),
        WET: ((86, 82, 62), (98, 92, 68), (108, 100, 74), (74, 72, 56)),
    },
    WORN_GRASS: {
        DRY: ((154, 134, 82), (168, 146, 92), (136, 122, 78), (178, 158, 108)),
        NORMAL: ((132, 112, 74), (146, 124, 84), (116, 104, 70), (156, 136, 96)),
        WET: ((90, 76, 58), (104, 86, 62), (116, 96, 70), (78, 66, 52)),
    },
    DIRT_PATH: {
        DRY: ((170, 136, 82), (184, 148, 92), (150, 120, 76), (196, 160, 106)),
        NORMAL: ((142, 104, 68), (156, 116, 76), (126, 94, 64), (168, 128, 88)),
        WET: ((86, 62, 50), (98, 70, 54), (112, 82, 62), (72, 54, 46)),
    },
    PATH: {
        DRY: ((184, 146, 88), (198, 158, 100), (164, 130, 82), (210, 170, 112)),
        NORMAL: ((152, 112, 72), (166, 124, 82), (136, 100, 66), (178, 136, 92)),
        WET: ((82, 58, 46), (96, 68, 52), (108, 78, 58), (70, 50, 42)),
    },
}

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


class TerrainPaletteManager:
    """Central palette source for terrain visuals."""

    def palette_for(self, state: TerrainVisualState) -> tuple[Color, ...]:
        if state.terrain in GRASSLAND_TERRAINS:
            season_palettes = GRASS_MOISTURE_PALETTES.get(state.visual_season or state.season, GRASS_MOISTURE_PALETTES["Spring"])
            palette = season_palettes.get(state.moisture_state or NORMAL, season_palettes[NORMAL])
            return self._terrain_adjusted_palette(palette, state.terrain)
        if state.terrain in PATH_TERRAINS:
            terrain_palettes = PATH_PALETTES.get(state.terrain, PATH_PALETTES[DIRT_PATH])
            return terrain_palettes.get(state.moisture_state or NORMAL, terrain_palettes[NORMAL])
        if state.terrain == "forest":
            return FOREST_SEASON_PALETTES.get(state.visual_season or state.season, FOREST_SEASON_PALETTES["Spring"])
        if state.terrain == "water":
            return WATER_WEATHER_PALETTES.get(state.weather_state or "Clear", WATER_WEATHER_PALETTES["Clear"])
        if state.gameplay and state.gameplay.construction_state:
            return CONSTRUCTION_PALETTES.get(state.gameplay.construction_state, CONSTRUCTION_PALETTES["Under Construction"])
        return self._generic_palette(state.base_color)

    def weights_for(self, state: TerrainVisualState, palette: tuple[Color, ...]) -> tuple[int, ...]:
        if state.terrain in GRASSLAND_TERRAINS:
            return GRASS_MOISTURE_WEIGHTS.get(state.moisture_state or NORMAL, GRASS_MOISTURE_WEIGHTS[NORMAL])
        if state.terrain in PATH_TERRAINS:
            return PATH_WEAR_WEIGHTS.get(state.terrain, PATH_WEAR_WEIGHTS[DIRT_PATH])
        if state.terrain == "forest":
            return FOREST_SEASON_WEIGHTS.get(state.visual_season or state.season, FOREST_SEASON_WEIGHTS["Spring"])
        if state.terrain == "water":
            return WATER_WEATHER_WEIGHTS.get(state.weather_state or "Clear", WATER_WEATHER_WEIGHTS["Clear"])
        if len(palette) == 4:
            return (34, 30, 22, 14)
        return tuple(1 for _ in palette)

    def _generic_palette(self, base_color: Color) -> tuple[Color, Color, Color, Color]:
        return (
            _shade(base_color, 0.94),
            base_color,
            _shade(base_color, 1.04),
            _shade(base_color, 0.98),
        )

    def _terrain_adjusted_palette(self, palette: tuple[Color, ...], terrain: str) -> tuple[Color, ...]:
        factors = GRASSLAND_PALETTE_FACTORS.get(terrain)
        if factors is None:
            return palette
        return tuple(_multiply_color(color, factors) for color in palette)


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
            result = self._blend_with_palette(result, FARM_STAGE_PALETTES.get(crop_visual_stage(gameplay.crop_state, gameplay.crop_growth, gameplay.crop_food)), 0.88)
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
    """Shared deterministic 2x2 pattern generator."""

    def subcell_colors(
        self,
        seed: int | None,
        tile_x: int,
        tile_y: int,
        state: TerrainVisualState,
        palette: tuple[Color, ...],
        weights: tuple[int, ...],
    ) -> tuple[Color, Color, Color, Color]:
        colors: list[Color] = []
        identity = self._state_identity(state)
        for subcell in range(4):
            roll = _stable_int(seed, tile_x, tile_y, state.terrain, identity, subcell)
            colors.append(_weighted_color(palette, weights, roll))
        if len(set(colors)) == 1 and len(palette) > 1:
            replacement_index = _stable_int(seed, tile_x, tile_y, state.terrain, identity, "variation") % len(palette)
            replacement = palette[replacement_index]
            if replacement == colors[0]:
                replacement = palette[(replacement_index + 1) % len(palette)]
            colors[-1] = replacement
        return tuple(colors)  # type: ignore[return-value]

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


class TerrainRenderer:
    """Shared terrain rendering pipeline for every map tile."""

    def __init__(
        self,
        palette_manager: TerrainPaletteManager | None = None,
        pattern_generator: TerrainPatternGenerator | None = None,
        modifier_stack: TerrainModifierStack | None = None,
    ) -> None:
        self.palette_manager = palette_manager or TerrainPaletteManager()
        self.pattern_generator = pattern_generator or TerrainPatternGenerator()
        self.modifier_stack = modifier_stack or TerrainModifierStack()

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

    def subcell_colors_for(self, context: TerrainRenderContext) -> tuple[Color, Color, Color, Color]:
        state = self.visual_state_for(context)
        palette = self.palette_manager.palette_for(state)
        palette = self.modifier_stack.apply(palette, state)
        weights = self.palette_manager.weights_for(state, palette)
        colors = self.pattern_generator.subcell_colors(
            getattr(context.world, "seed", None),
            context.tile_x,
            context.tile_y,
            state,
            palette,
            weights,
        )
        if state.environment_tinted:
            events = getattr(context.world, "active_environment_events", ())
            return tuple(environmental_tile_color(color, state.terrain, events) for color in colors)  # type: ignore[return-value]
        return colors

    def draw_tile(self, surface: pygame.Surface, rect: pygame.Rect, context: TerrainRenderContext) -> None:
        half = max(1, TILE_SIZE // 2)
        x = rect.x
        y = rect.y
        sub_rects = (
            pygame.Rect(x, y, half, half),
            pygame.Rect(x + half, y, rect.width - half, half),
            pygame.Rect(x, y + half, half, rect.height - half),
            pygame.Rect(x + half, y + half, rect.width - half, rect.height - half),
        )
        for sub_rect, color in zip(sub_rects, self.subcell_colors_for(context)):
            pygame.draw.rect(surface, color, sub_rect)


def _shade(color: Color, factor: float) -> Color:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)  # type: ignore[return-value]


def _multiply_color(color: Color, factors: tuple[float, float, float]) -> Color:
    return tuple(max(0, min(255, int(channel * factor))) for channel, factor in zip(color, factors))  # type: ignore[return-value]


def _mix_color(color: Color, target: Color, strength: float) -> Color:
    strength = max(0.0, min(1.0, strength))
    return tuple(round(channel + (target_channel - channel) * strength) for channel, target_channel in zip(color, target))  # type: ignore[return-value]


def _mix_palette_with_color(palette: tuple[Color, ...], target: Color, strength: float) -> tuple[Color, ...]:
    return tuple(_mix_color(color, target, strength) for color in palette)


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
