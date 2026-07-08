from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.config import (
    MYSTERY_CHANCE_PER_DAY,
    MYSTERY_MAX_DURATION_DAYS,
    MYSTERY_MIN_DURATION_DAYS,
    MYSTERY_WITNESS_RADIUS,
)
from src.social_memory import chebyshev_distance, villager_key
from src.world_history import MYSTERY

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


STRANGE_LIGHTS = "strange_lights"


@dataclass(frozen=True)
class MysteryProfile:
    mystery_type: str
    title: str
    destination_label: str
    chronicle_title: str
    memory_text: str


@dataclass
class ActiveMystery:
    mystery_type: str
    title: str
    anchor: tuple[int, int]
    location_label: str
    duration_days: int
    remaining_days: int
    witnessed_by: set[str] = field(default_factory=set)
    chronicle_recorded: bool = False


MYSTERY_PROFILES = {
    STRANGE_LIGHTS: MysteryProfile(
        mystery_type=STRANGE_LIGHTS,
        title="Strange Lights",
        destination_label="Mystery: Strange Lights",
        chronicle_title="Strange Lights",
        memory_text="Saw strange lights that no one could explain.",
    ),
}


def update_mysteries(world: World, rng) -> None:
    for mystery in list(getattr(world, "active_mysteries", [])):
        mystery.remaining_days -= 1
        record_mystery_witnesses(world, mystery)
        if mystery.remaining_days <= 0:
            world.active_mysteries.remove(mystery)

    maybe_start_mystery(world, rng)


def maybe_start_mystery(world: World, rng) -> ActiveMystery | None:
    if any(mystery.mystery_type == STRANGE_LIGHTS for mystery in getattr(world, "active_mysteries", [])):
        return None
    if rng.random() >= MYSTERY_CHANCE_PER_DAY:
        return None

    anchor_info = choose_strange_lights_location(world, rng)
    if anchor_info is None:
        return None
    anchor, location_label = anchor_info
    duration = rng.randint(MYSTERY_MIN_DURATION_DAYS, MYSTERY_MAX_DURATION_DAYS)
    profile = MYSTERY_PROFILES[STRANGE_LIGHTS]
    mystery = ActiveMystery(
        mystery_type=STRANGE_LIGHTS,
        title=profile.title,
        anchor=anchor,
        location_label=location_label,
        duration_days=duration,
        remaining_days=duration,
    )
    world.active_mysteries.append(mystery)
    record_mystery_history(world, mystery)
    record_mystery_witnesses(world, mystery)
    return mystery


def choose_strange_lights_location(world: World, rng) -> tuple[tuple[int, int], str] | None:
    candidates: list[tuple[int, tuple[int, int], str]] = []
    for y, row in enumerate(world.tiles):
        for x, tile in enumerate(row):
            if tile.kind == "water":
                label = "the lake" if _nearby_water_count(world, x, y) >= 8 else "the river"
                candidates.append((42, (x, y), label))
            elif tile.kind == "forest" and _has_neighbor_kind(world, x, y, {"grass", "plain"}):
                candidates.append((28, (x, y), "the forest edge"))
            elif tile.kind in {"grass", "plain"} and _open_neighbour_count(world, x, y) >= 6:
                candidates.append((18, (x, y), "an open meadow"))

    if not candidates:
        return None

    total = sum(weight for weight, _, _ in candidates)
    roll = rng.random() * total
    running = 0.0
    for weight, pos, label in candidates:
        running += weight
        if roll <= running:
            return pos, label
    return candidates[-1][1], candidates[-1][2]


def record_mystery_history(world: World, mystery: ActiveMystery) -> None:
    if mystery.chronicle_recorded:
        return
    mystery.chronicle_recorded = True
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=MYSTERY,
        title=MYSTERY_PROFILES[mystery.mystery_type].chronicle_title,
        description=f"Several villagers reported strange lights near {mystery.location_label}.",
    )


def record_mystery_witnesses(world: World, mystery: ActiveMystery) -> list[Agent]:
    witnesses = mystery_witnesses(world, mystery)
    memory = MYSTERY_PROFILES[mystery.mystery_type].memory_text
    for agent in witnesses:
        key = villager_key(agent)
        if key in mystery.witnessed_by:
            continue
        mystery.witnessed_by.add(key)
        if memory not in agent.personal_memories:
            agent.personal_memories.insert(0, memory)
    return witnesses


def mystery_witnesses(world: World, mystery: ActiveMystery) -> list[Agent]:
    ax, ay = mystery.anchor
    return [
        agent
        for agent in world.living_agents()
        if chebyshev_distance(agent.x, agent.y, ax, ay) <= MYSTERY_WITNESS_RADIUS
    ]


def mystery_destination(world: World) -> tuple[str, tuple[int, int]] | None:
    mystery = active_strange_lights(world)
    if mystery is None:
        return None
    return MYSTERY_PROFILES[mystery.mystery_type].destination_label, mystery.anchor


def mystery_attraction(agent: Agent, world: World) -> float:
    mystery = active_strange_lights(world)
    if mystery is None:
        return 0.0
    distance = chebyshev_distance(agent.x, agent.y, mystery.anchor[0], mystery.anchor[1])
    return max(0.0, 64.0 - distance * 3.0)


def active_strange_lights(world: World) -> ActiveMystery | None:
    for mystery in getattr(world, "active_mysteries", []):
        if mystery.mystery_type == STRANGE_LIGHTS:
            return mystery
    return None


def active_mystery_at(world: World, center: tuple[int, int], radius: int = 2) -> ActiveMystery | None:
    for mystery in getattr(world, "active_mysteries", []):
        if chebyshev_distance(center[0], center[1], mystery.anchor[0], mystery.anchor[1]) <= radius:
            return mystery
    return None


def mystery_diagnostics(world: World) -> list[tuple[str, object]]:
    active = list(getattr(world, "active_mysteries", []))
    witnesses = sum(len(getattr(mystery, "witnessed_by", set())) for mystery in active)
    names = ", ".join(mystery.title for mystery in active) or "None"
    return [
        ("Active Mysteries", names),
        ("Mystery Count", len(active)),
        ("Witnesses", witnesses),
    ]


def _has_neighbor_kind(world: World, x: int, y: int, kinds: set[str]) -> bool:
    for nx, ny in _neighbor_positions(world, x, y):
        if world.tile_at(nx, ny).kind in kinds:
            return True
    return False


def _nearby_water_count(world: World, x: int, y: int) -> int:
    count = 0
    for ny in range(max(0, y - 2), min(world.height, y + 3)):
        for nx in range(max(0, x - 2), min(world.width, x + 3)):
            if world.tile_at(nx, ny).kind == "water":
                count += 1
    return count


def _open_neighbour_count(world: World, x: int, y: int) -> int:
    count = 0
    for nx, ny in _neighbor_positions(world, x, y, diagonals=True):
        tile = world.tile_at(nx, ny)
        if tile.walkable and tile.kind in {"grass", "plain"}:
            count += 1
    return count


def _neighbor_positions(world: World, x: int, y: int, diagonals: bool = False) -> list[tuple[int, int]]:
    offsets = [
        (0, 1),
        (1, 0),
        (0, -1),
        (-1, 0),
    ]
    if diagonals:
        offsets.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    positions = []
    for dx, dy in offsets:
        nx = x + dx
        ny = y + dy
        if 0 <= nx < world.width and 0 <= ny < world.height:
            positions.append((nx, ny))
    return positions
