from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.config import SETTLEMENT_RADIUS


@dataclass
class Settlement:
    name: str
    x: int
    y: int
    founded_day: int
    founded_season: str
    radius: int = SETTLEMENT_RADIUS
    population: int = 0


def found_settlement(world) -> Settlement:
    center_x, center_y = _agent_centroid(world.agents)
    x, y = nearest_walkable_tile(world, center_x, center_y)
    return Settlement(
        name=settlement_name(world),
        x=x,
        y=y,
        founded_day=world.day,
        founded_season=world.season,
        population=len(world.living_agents()),
    )


def nearest_walkable_tile(world, center_x: int, center_y: int) -> tuple[int, int]:
    start_x = max(0, min(world.width - 1, center_x))
    start_y = max(0, min(world.height - 1, center_y))

    if world.tile_at(start_x, start_y).walkable:
        return start_x, start_y

    max_radius = max(world.width, world.height)
    for radius in range(1, max_radius + 1):
        candidates = []
        for y in range(max(0, start_y - radius), min(world.height, start_y + radius + 1)):
            for x in range(max(0, start_x - radius), min(world.width, start_x + radius + 1)):
                if max(abs(x - start_x), abs(y - start_y)) != radius:
                    continue
                if world.tile_at(x, y).walkable:
                    candidates.append((x, y))

        if candidates:
            return min(candidates, key=lambda pos: (abs(pos[0] - center_x) + abs(pos[1] - center_y), pos[1], pos[0]))

    return start_x, start_y


def settlement_name(world) -> str:
    identity = world.identity
    title = identity.title if identity is not None else "Colony"
    tags = identity.tags if identity is not None else []
    root = _name_root(title)

    suffixes = _suffixes_for_tags(tags)
    suffix = suffixes[_deterministic_index(world.seed, title, tags, len(suffixes))]
    return f"{root}{suffix}"


def _agent_centroid(agents) -> tuple[int, int]:
    if not agents:
        return 0, 0

    x = round(sum(agent.x for agent in agents) / len(agents))
    y = round(sum(agent.y for agent in agents) / len(agents))
    return x, y


def _name_root(title: str) -> str:
    first_word = title.replace("The ", "").split()[0]
    for suffix in ("mere", "vein", "scar", "wood", "deep", "stone", "water", "fen"):
        if first_word.lower().endswith(suffix):
            return first_word[:-len(suffix)].capitalize() or first_word
    return first_word.capitalize()


def _suffixes_for_tags(tags: list[str]) -> list[str]:
    if "marshland" in tags or "wet" in tags:
        return ["haven", "watch", "mere"]
    if "forested" in tags:
        return ["hold", "watch", "haven"]
    if "dry" in tags or "thirsty" in tags:
        return ["hold", "watch", "rest"]
    if "mountainous" in tags or "rugged" in tags:
        return ["watch", "hold", "crest"]
    if "harsh" in tags or "resource_poor" in tags:
        return ["watch", "hold", "haven"]
    return ["hold", "haven", "watch"]


def _deterministic_index(seed, title: str, tags: list[str], count: int) -> int:
    key = f"{seed}|{title}|{','.join(tags)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % count
