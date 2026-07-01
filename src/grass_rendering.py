from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.config import GRASS_MOISTURE_TRANSITION_HOURS, TICKS_PER_HOUR


Color = tuple[int, int, int]

DRY = "Dry"
NORMAL = "Normal"
WET = "Wet"

CLEAR = "clear"
RAIN = "rain"
HEAVY_RAIN = "heavy_rain"
DROUGHT = "drought"

GRASS_MOISTURE_PALETTES: dict[str, dict[str, tuple[Color, ...]]] = {
    "Spring": {
        DRY: ((108, 156, 74), (118, 168, 82), (132, 178, 88), (148, 188, 96)),
        NORMAL: ((70, 148, 70), (84, 164, 76), (98, 178, 82), (118, 192, 92)),
        WET: ((48, 124, 62), (58, 142, 68), (72, 160, 78), (88, 176, 88)),
    },
    "Summer": {
        DRY: ((138, 136, 62), (154, 142, 68), (124, 126, 66), (166, 152, 84)),
        NORMAL: ((82, 136, 64), (94, 146, 70), (104, 154, 76), (116, 158, 82)),
        WET: ((42, 108, 56), (50, 126, 64), (62, 142, 70), (72, 152, 78)),
    },
    "Autumn": {
        DRY: ((126, 112, 58), (142, 118, 64), (112, 104, 60), (150, 132, 76)),
        NORMAL: ((92, 124, 62), (108, 132, 66), (126, 136, 70), (142, 128, 70)),
        WET: ((58, 104, 58), (72, 120, 62), (88, 132, 68), (110, 136, 70)),
    },
    "Winter": {
        DRY: ((148, 144, 116), (156, 150, 124), (134, 136, 112), (166, 158, 134)),
        NORMAL: ((118, 130, 108), (132, 140, 118), (144, 148, 128), (104, 120, 96)),
        WET: ((82, 102, 82), (94, 116, 92), (108, 126, 102), (116, 128, 110)),
    },
}

GRASS_MOISTURE_WEIGHTS: dict[str, tuple[int, ...]] = {
    DRY: (34, 28, 24, 14),
    NORMAL: (30, 34, 24, 12),
    WET: (32, 32, 24, 12),
}


@dataclass
class GrassMoistureTransitionState:
    previous_mode: str = CLEAR
    current_mode: str = CLEAR
    transition_start_tick: int = 0
    transition_id: int = 0

    def update(self, new_mode: str, world_tick: int) -> None:
        if new_mode == self.current_mode:
            return
        self.previous_mode = self.current_mode
        self.current_mode = new_mode
        self.transition_start_tick = world_tick
        self.transition_id += 1


def grass_moisture_mode_for_events(events) -> str:
    effect_types = {getattr(event, "effect_type", None) for event in events}
    if "heavy_rain" in effect_types:
        return HEAVY_RAIN
    if "rain" in effect_types:
        return RAIN
    if "drought" in effect_types:
        return DROUGHT
    return CLEAR


def grass_transition_cache_key(state: GrassMoistureTransitionState, world_tick: int) -> tuple[str, str, int, int]:
    if state.previous_mode == state.current_mode:
        elapsed = 0
    else:
        elapsed = min(transition_duration_ticks(), transition_elapsed_ticks(state, world_tick))
    return (state.previous_mode, state.current_mode, state.transition_id, elapsed)


def grass_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    season: str,
    base_moisture: float | None,
    state: GrassMoistureTransitionState,
    world_tick: int,
) -> tuple[Color, Color, Color, Color]:
    visual_mode = grass_visual_moisture_mode(seed, tile_x, tile_y, state, world_tick)
    moisture_state = grass_moisture_state(base_moisture, visual_mode)
    return _grass_subcell_colors(seed, tile_x, tile_y, season, moisture_state)


def grass_visual_moisture_mode(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    state: GrassMoistureTransitionState,
    world_tick: int,
) -> str:
    if state.previous_mode == state.current_mode:
        return state.current_mode
    elapsed = transition_elapsed_ticks(state, world_tick)
    if elapsed >= grass_transition_tick(seed, tile_x, tile_y, state.current_mode, state.transition_id):
        return state.current_mode
    return state.previous_mode


def grass_moisture_state(base_moisture: float | None, visual_mode: str) -> str:
    if visual_mode in (RAIN, HEAVY_RAIN):
        return WET
    if visual_mode == DROUGHT:
        return DRY

    moisture = 0.5 if base_moisture is None else max(0.0, min(1.0, base_moisture))
    if moisture < 0.38:
        return DRY
    if moisture > 0.62:
        return WET
    return NORMAL


def grass_transition_tick(seed: int | None, tile_x: int, tile_y: int, mode: str, transition_id: int) -> int:
    duration = max(1, transition_duration_ticks())
    return _stable_int(seed, tile_x, tile_y, mode, transition_id, "grass-transition") % (duration + 1)


def transition_elapsed_ticks(state: GrassMoistureTransitionState, world_tick: int) -> int:
    return max(0, world_tick - state.transition_start_tick)


def transition_duration_ticks() -> int:
    return max(1, GRASS_MOISTURE_TRANSITION_HOURS * TICKS_PER_HOUR)


def _grass_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    season: str,
    moisture_state: str,
) -> tuple[Color, Color, Color, Color]:
    season_palettes = GRASS_MOISTURE_PALETTES.get(season, GRASS_MOISTURE_PALETTES["Spring"])
    palette = season_palettes.get(moisture_state, season_palettes[NORMAL])
    weights = GRASS_MOISTURE_WEIGHTS.get(moisture_state, GRASS_MOISTURE_WEIGHTS[NORMAL])
    colors = []
    for subcell in range(4):
        roll = _stable_int(seed, tile_x, tile_y, season, moisture_state, subcell)
        colors.append(_weighted_color(palette, weights, roll))
    return tuple(colors)  # type: ignore[return-value]


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
