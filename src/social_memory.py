from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


STRANGER = "Stranger"
SEEN = "Seen"
ACQUAINTED = "Acquainted"
FAMILIAR = "Familiar"

SEEN_THRESHOLD = 2
ACQUAINTED_THRESHOLD = 10
FAMILIAR_THRESHOLD = 30
SOCIAL_MEMORY_RADIUS = 4


@dataclass
class SocialMemoryEntry:
    villager_id: str
    display_name: str
    familiarity_score: int = 0
    last_seen_day: int = 0


def villager_key(agent: Agent) -> str:
    return agent.agent_id or agent.name


def familiarity_level(score: int) -> str:
    if score >= FAMILIAR_THRESHOLD:
        return FAMILIAR
    if score >= ACQUAINTED_THRESHOLD:
        return ACQUAINTED
    if score >= SEEN_THRESHOLD:
        return SEEN
    return STRANGER


def record_observation(observer: Agent, other: Agent, day: int):
    key = villager_key(other)
    entry = observer.social_memory.get(key)
    if entry is None:
        entry = SocialMemoryEntry(
            villager_id=key,
            display_name=other.name,
        )
        observer.social_memory[key] = entry

    entry.display_name = other.name
    entry.familiarity_score += 1
    entry.last_seen_day = day


def update_social_memory(world: World, radius: int = SOCIAL_MEMORY_RADIUS):
    from src.config import SOCIAL_MEMORY_MAX_OBSERVATIONS_PER_AGENT

    living_agents = world.living_agents()
    by_tile = {(agent.x, agent.y): [] for agent in living_agents}
    for agent in living_agents:
        by_tile[(agent.x, agent.y)].append(agent)

    for observer in living_agents:
        observed = 0
        for other in nearby_agents(observer, by_tile, radius):
            if other is observer:
                continue
            record_observation(observer, other, world.day)
            observed += 1
            if observed >= SOCIAL_MEMORY_MAX_OBSERVATIONS_PER_AGENT:
                break


def nearby_agents(
    observer: Agent,
    by_tile: dict[tuple[int, int], list[Agent]],
    radius: int,
) -> list[Agent]:
    nearby: list[tuple[int, str, Agent]] = []
    for y in range(observer.y - radius, observer.y + radius + 1):
        for x in range(observer.x - radius, observer.x + radius + 1):
            distance = chebyshev_distance(observer.x, observer.y, x, y)
            if distance > radius:
                continue
            for agent in by_tile.get((x, y), []):
                nearby.append((distance, villager_key(agent), agent))

    nearby.sort(key=lambda item: (item[0], item[1]))
    return [agent for _, _, agent in nearby]


def familiarity_summary(agent: Agent, limit: int = 3) -> list[str]:
    entries = [
        entry
        for entry in agent.social_memory.values()
        if familiarity_level(entry.familiarity_score) != STRANGER
    ]
    entries.sort(key=lambda entry: (-entry.familiarity_score, entry.display_name))
    return [
        f"{entry.display_name} ({familiarity_level(entry.familiarity_score)})"
        for entry in entries[:limit]
    ]


def chebyshev_distance(ax: int, ay: int, bx: int, by: int) -> int:
    return max(abs(ax - bx), abs(ay - by))
