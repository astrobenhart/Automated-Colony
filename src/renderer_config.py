from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


Color = tuple[int, int, int]


@dataclass(frozen=True)
class AmbientOcclusionConfig:
    forest_receivers: tuple[str, ...]
    first_microtile_darken: float
    second_microtile_darken: float
    density_bonus: float
    max_density_bonus: float
    first_microtile_chance: int
    second_microtile_chance: int
    density_chance_bonus: int
    max_chance_bonus: int


@dataclass(frozen=True)
class PathVisualLanguageConfig:
    edge_shaping_enabled: bool
    encroachment_enabled: bool
    forest_encroachment_chance: int
    forest_encroachment_strength: float
    encroachment_terrains: tuple[str, ...]


@dataclass(frozen=True)
class SpritePipelineConfig:
    reserved_layers: tuple[str, ...]
    seasonal_tinting: bool
    environmental_tinting: bool


@dataclass(frozen=True)
class RendererArtConfig:
    master_vegetation_palettes: dict[str, tuple[Color, ...]]
    vegetation_harmony_strength: dict[str, float]
    terrain_palette_factors: dict[str, tuple[float, float, float]]
    terrain_motifs: dict[str, tuple[str, ...]]
    path_palettes: dict[str, dict[str, tuple[Color, ...]]]
    ambient_occlusion: AmbientOcclusionConfig
    path_visual_language: PathVisualLanguageConfig
    sprite_pipeline: SpritePipelineConfig
    source_path: Path


DEFAULT_RENDERER_CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "rendering" / "default.json"


@lru_cache(maxsize=4)
def load_renderer_art_config(path: str | Path = DEFAULT_RENDERER_CONFIG_PATH) -> RendererArtConfig:
    source_path = Path(path)
    with source_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    ambient = data["ambient_occlusion"]
    path_visual = data["path_visual_language"]
    sprite_pipeline = data["sprite_pipeline"]
    return RendererArtConfig(
        master_vegetation_palettes={
            season: tuple(_color(color) for color in palette)
            for season, palette in data["master_vegetation_palettes"].items()
        },
        vegetation_harmony_strength={
            season: float(strength)
            for season, strength in data["vegetation_harmony_strength"].items()
        },
        terrain_palette_factors={
            terrain: _factor_tuple(factors)
            for terrain, factors in data["terrain_palette_factors"].items()
        },
        terrain_motifs={
            terrain: tuple(str(motif) for motif in motifs)
            for terrain, motifs in data["terrain_motifs"].items()
        },
        path_palettes={
            terrain: {
                moisture: tuple(_color(color) for color in palette)
                for moisture, palette in moisture_palettes.items()
            }
            for terrain, moisture_palettes in data["path_palettes"].items()
        },
        ambient_occlusion=AmbientOcclusionConfig(
            forest_receivers=tuple(str(kind) for kind in ambient["forest_receivers"]),
            first_microtile_darken=float(ambient["first_microtile_darken"]),
            second_microtile_darken=float(ambient["second_microtile_darken"]),
            density_bonus=float(ambient["density_bonus"]),
            max_density_bonus=float(ambient["max_density_bonus"]),
            first_microtile_chance=int(ambient["first_microtile_chance"]),
            second_microtile_chance=int(ambient["second_microtile_chance"]),
            density_chance_bonus=int(ambient["density_chance_bonus"]),
            max_chance_bonus=int(ambient["max_chance_bonus"]),
        ),
        path_visual_language=PathVisualLanguageConfig(
            edge_shaping_enabled=bool(path_visual["edge_shaping_enabled"]),
            encroachment_enabled=bool(path_visual["encroachment_enabled"]),
            forest_encroachment_chance=int(path_visual["forest_encroachment_chance"]),
            forest_encroachment_strength=float(path_visual["forest_encroachment_strength"]),
            encroachment_terrains=tuple(str(kind) for kind in path_visual["encroachment_terrains"]),
        ),
        sprite_pipeline=SpritePipelineConfig(
            reserved_layers=tuple(str(layer) for layer in sprite_pipeline["reserved_layers"]),
            seasonal_tinting=bool(sprite_pipeline["seasonal_tinting"]),
            environmental_tinting=bool(sprite_pipeline["environmental_tinting"]),
        ),
        source_path=source_path,
    )


def _color(value: Any) -> Color:
    red, green, blue = value
    return int(red), int(green), int(blue)


def _factor_tuple(value: Any) -> tuple[float, float, float]:
    red, green, blue = value
    return float(red), float(green), float(blue)
