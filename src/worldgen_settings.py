from __future__ import annotations

from dataclasses import dataclass, replace

from src.config import (
    ENV_EVENT_CHANCE_PER_DAY,
    HEIGHT,
    RIVER_COUNT,
    WILDLIFE_DENSITY,
    WIDTH,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class WorldGenSettings:
    seed: int | None = None
    width: int = WIDTH
    height: int = HEIGHT
    water_level: float = 0.28
    forest_density: float = 0.50
    climate_harshness: float = 0.0
    mountain_level: float = 0.74
    river_count: int = RIVER_COUNT
    wildlife_density: float = WILDLIFE_DENSITY
    event_frequency: float = ENV_EVENT_CHANCE_PER_DAY
    resource_abundance: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, "width", max(1, int(self.width)))
        object.__setattr__(self, "height", max(1, int(self.height)))
        object.__setattr__(self, "water_level", _clamp(float(self.water_level)))
        object.__setattr__(self, "forest_density", _clamp(float(self.forest_density)))
        object.__setattr__(self, "climate_harshness", _clamp(float(self.climate_harshness)))
        object.__setattr__(self, "mountain_level", _clamp(float(self.mountain_level)))
        object.__setattr__(self, "river_count", max(0, int(self.river_count)))
        object.__setattr__(self, "wildlife_density", _clamp(float(self.wildlife_density)))
        object.__setattr__(self, "event_frequency", _clamp(float(self.event_frequency)))
        object.__setattr__(self, "resource_abundance", _clamp(float(self.resource_abundance)))

    def with_overrides(self, **kwargs) -> "WorldGenSettings":
        return replace(self, **{key: value for key, value in kwargs.items() if value is not None})


WORLD_PRESETS = {
    "normal": WorldGenSettings(),
    "wet": WorldGenSettings(
        water_level=0.34,
        forest_density=0.62,
        climate_harshness=0.0,
        resource_abundance=1.0,
    ),
    "dry": WorldGenSettings(
        water_level=0.22,
        forest_density=0.32,
        climate_harshness=0.40,
        resource_abundance=0.80,
    ),
    "forest": WorldGenSettings(
        water_level=0.28,
        forest_density=0.86,
        climate_harshness=0.0,
        resource_abundance=1.0,
    ),
    "harsh": WorldGenSettings(
        water_level=0.24,
        forest_density=0.34,
        climate_harshness=0.85,
        wildlife_density=0.006,
        event_frequency=0.10,
        resource_abundance=0.60,
    ),
}


def default_worldgen_settings() -> WorldGenSettings:
    return WORLD_PRESETS["normal"]
