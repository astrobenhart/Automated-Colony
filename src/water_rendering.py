from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.config import TICKS_PER_HOUR, WATER_WEATHER_TRANSITION_HOURS


Color = tuple[int, int, int]

CLEAR = "Clear"
RAIN = "Rain"
HEAVY_RAIN = "Heavy Rain"

WATER_WEATHER_PALETTES: dict[str, tuple[Color, ...]] = {
    CLEAR: (
        (34, 82, 156),
        (42, 96, 176),
        (54, 112, 190),
        (70, 128, 202),
    ),
    RAIN: (
        (42, 92, 166),
        (56, 112, 184),
        (76, 132, 196),
        (92, 128, 162),
        (62, 104, 144),
    ),
    HEAVY_RAIN: (
        (26, 66, 134),
        (38, 86, 164),
        (72, 126, 204),
        (96, 154, 224),
        (44, 82, 116),
        (112, 152, 184),
    ),
}

WATER_WEATHER_WEIGHTS: dict[str, tuple[int, ...]] = {
    CLEAR: (34, 34, 22, 10),
    RAIN: (24, 28, 22, 16, 10),
    HEAVY_RAIN: (24, 24, 18, 14, 12, 8),
}


@dataclass
class WaterTransitionState:
    previous_state: str = CLEAR
    current_state: str = CLEAR
    transition_start_tick: int = 0
    transition_id: int = 0

    def update(self, new_state: str, world_tick: int) -> None:
        if new_state == self.current_state:
            return
        self.previous_state = self.current_state
        self.current_state = new_state
        self.transition_start_tick = world_tick
        self.transition_id += 1


def weather_state_for_events(events) -> str:
    effect_types = {getattr(event, "effect_type", None) for event in events}
    if "heavy_rain" in effect_types:
        return HEAVY_RAIN
    if "rain" in effect_types:
        return RAIN
    return CLEAR


def water_transition_cache_key(state: WaterTransitionState, world_tick: int) -> tuple[str, str, int, int]:
    if state.previous_state == state.current_state:
        elapsed = 0
    else:
        elapsed = min(transition_duration_ticks(), transition_elapsed_ticks(state, world_tick))
    return (
        state.previous_state,
        state.current_state,
        state.transition_id,
        elapsed,
    )


def water_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    state: WaterTransitionState,
    world_tick: int,
) -> tuple[Color, Color, Color, Color]:
    visual_weather = water_visual_weather(seed, tile_x, tile_y, state, world_tick)
    return _weather_subcell_colors(seed, tile_x, tile_y, visual_weather)


def water_visual_weather(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    state: WaterTransitionState,
    world_tick: int,
) -> str:
    if state.previous_state == state.current_state:
        return state.current_state
    elapsed = transition_elapsed_ticks(state, world_tick)
    if elapsed >= water_transition_tick(seed, tile_x, tile_y, state.current_state, state.transition_id):
        return state.current_state
    return state.previous_state


def water_transition_tick(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    weather_state: str,
    transition_id: int,
) -> int:
    duration = max(1, transition_duration_ticks())
    return _stable_int(seed, tile_x, tile_y, weather_state, transition_id, "water-transition") % (duration + 1)


def transition_elapsed_ticks(state: WaterTransitionState, world_tick: int) -> int:
    return max(0, world_tick - state.transition_start_tick)


def transition_duration_ticks() -> int:
    return max(1, WATER_WEATHER_TRANSITION_HOURS * TICKS_PER_HOUR)


def _weather_subcell_colors(
    seed: int | None,
    tile_x: int,
    tile_y: int,
    weather_state: str,
) -> tuple[Color, Color, Color, Color]:
    palette = WATER_WEATHER_PALETTES.get(weather_state, WATER_WEATHER_PALETTES[CLEAR])
    weights = WATER_WEATHER_WEIGHTS.get(weather_state, WATER_WEATHER_WEIGHTS[CLEAR])
    colors = []
    for subcell in range(4):
        roll = _stable_int(seed, tile_x, tile_y, weather_state, subcell)
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
