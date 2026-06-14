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
    living_agents = world.living_agents()
    for index, observer in enumerate(living_agents):
        for other in living_agents[index + 1:]:
            if chebyshev_distance(observer.x, observer.y, other.x, other.y) <= radius:
                record_observation(observer, other, world.day)
                record_observation(other, observer, world.day)


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
