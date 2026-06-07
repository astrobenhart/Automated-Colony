from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field


SURVIVAL_OUTLOOKS = ["Gentle", "Favorable", "Fair", "Uncertain", "Harsh", "Slim", "Grim"]


@dataclass(frozen=True)
class WorldIdentity:
    title: str
    subtitle: str
    survival_outlook: str
    tags: list[str] = field(default_factory=list)


def generate_world_identity(world) -> WorldIdentity:
    metrics = analyze_world(world)
    tags = classify_world(metrics, world.settings)
    outlook = survival_outlook(metrics, world.settings)
    title = generate_title(tags, world.seed, world.settings)
    subtitle = generate_subtitle(tags, outlook)
    return WorldIdentity(title=title, subtitle=subtitle, survival_outlook=outlook, tags=tags)


def analyze_world(world) -> dict[str, float]:
    total_tiles = max(1, world.width * world.height)
    terrain = Counter(tile.kind for row in world.tiles for tile in row)
    food = world.total_food_on_map()
    wood = world.total_wood_on_map()
    walkable = sum(1 for row in world.tiles for tile in row if tile.walkable)

    return {
        "water_pct": terrain["water"] / total_tiles,
        "forest_pct": terrain["forest"] / total_tiles,
        "wetland_pct": terrain["wetland"] / total_tiles,
        "dry_pct": terrain["dry"] / total_tiles,
        "mountain_pct": terrain["mountain"] / total_tiles,
        "walkable_pct": walkable / total_tiles,
        "food_per_tile": food / total_tiles,
        "wood_per_tile": wood / total_tiles,
        "wildlife_per_tile": len([animal for animal in world.animals if animal.alive]) / total_tiles,
    }


def classify_world(metrics: dict[str, float], settings) -> list[str]:
    tags: list[str] = []

    if metrics["water_pct"] >= 0.09:
        tags.append("wet")
    if metrics["wetland_pct"] >= 0.07 or (metrics["water_pct"] >= 0.08 and metrics["wetland_pct"] >= 0.035):
        tags.append("marshland")
    if metrics["forest_pct"] >= 0.18:
        tags.append("forested")
    if metrics["wood_per_tile"] >= 0.55:
        tags.append("wood_rich")
    if metrics["dry_pct"] >= 0.25:
        tags.append("dry")
    if metrics["water_pct"] < 0.045 and metrics["dry_pct"] >= 0.18:
        tags.append("thirsty")
    if metrics["mountain_pct"] >= 0.12:
        tags.extend(["rugged", "mountainous"])
    if metrics["food_per_tile"] < 0.055:
        tags.append("resource_poor")
    elif metrics["food_per_tile"] >= 0.12 and settings.climate_harshness < 0.45:
        tags.append("fertile")
    if settings.climate_harshness >= 0.55:
        tags.append("harsh")
    if metrics["wildlife_per_tile"] >= 0.010:
        tags.append("wildlife_rich")
    if not tags:
        tags.append("temperate")

    return _unique(tags)


def survival_outlook(metrics: dict[str, float], settings) -> str:
    score = 0.0
    score += min(2.5, metrics["food_per_tile"] * 12.0)
    score += min(2.0, metrics["wood_per_tile"] * 2.0)
    score += min(1.5, metrics["water_pct"] * 12.0)
    score += min(1.0, metrics["walkable_pct"])
    score -= metrics["dry_pct"] * 3.0
    score -= metrics["mountain_pct"] * 1.4
    score -= settings.climate_harshness * 2.1
    score += (settings.resource_abundance - 0.7) * 1.0

    if score >= 5.4:
        return "Gentle"
    if score >= 4.5:
        return "Favorable"
    if score >= 3.6:
        return "Fair"
    if score >= 2.7:
        return "Uncertain"
    if score >= 1.8:
        return "Harsh"
    if score >= 0.9:
        return "Slim"
    return "Grim"


def generate_title(tags: list[str], seed, settings) -> str:
    if "marshland" in tags or "wet" in tags:
        names = ["Rainvein Marsh", "Frostmere Basin", "Thornfen Reach", "Willowmere", "Ashen Fen"]
    elif "forested" in tags:
        names = ["Deepwood Vale", "Mossdeep Hollow", "The Greenwilds", "Willowmere", "Cedarfen Vale"]
    elif "dry" in tags or "thirsty" in tags:
        names = ["Sunscar Steppe", "Dustwillow Basin", "The Pale Lowlands", "Ashen Reach", "Drymere Flats"]
    elif "mountainous" in tags or "rugged" in tags:
        names = ["Greystone Meadow", "Coldwater Vale", "Stonebriar Basin", "The Grey Uplands", "Ridgefall Hollow"]
    elif "harsh" in tags or "resource_poor" in tags:
        names = ["Frostmere Basin", "The Pale Lowlands", "Ashen Fen", "Coldwater Vale", "Thornfen Reach"]
    else:
        names = ["Willowmere", "Greystone Meadow", "Mossdeep Hollow", "Coldwater Vale", "The Greenwilds"]

    return names[_deterministic_index(names, seed, settings, tags)]


def generate_subtitle(tags: list[str], outlook: str) -> str:
    if "marshland" in tags:
        return "Wet lowlands where rivers feed moss and reed."
    if "forested" in tags and "resource_poor" in tags:
        return "A wooded basin rich in timber but thin on food."
    if "forested" in tags:
        return "Dense forests with steady timber and sheltered paths."
    if "dry" in tags or "thirsty" in tags:
        return "A dry open world where water shapes survival."
    if "mountainous" in tags or "rugged" in tags:
        return "Rugged highlands where shelter is hard-won."
    if "harsh" in tags or outlook in ("Slim", "Grim"):
        return "A hard country of sparse food and sharp seasons."
    if "fertile" in tags:
        return "Gentle riverlands with steady food and timber."
    return "A temperate land of mixed woods and open ground."


def _deterministic_index(names: list[str], seed, settings, tags: list[str]) -> int:
    key = f"{seed}|{settings.width}x{settings.height}|{settings.water_level}|{settings.forest_density}|{settings.climate_harshness}|{','.join(tags)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % len(names)


def _unique(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
