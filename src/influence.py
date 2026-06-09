from __future__ import annotations

from typing import TYPE_CHECKING

from src.lifecycle import ELDER
from src.social_memory import ACQUAINTED, FAMILIAR, SEEN, familiarity_level, villager_key

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


LOW = "Low"
EMERGING = "Emerging"
NOTABLE = "Notable"
RESPECTED = "Respected"

INFLUENCE_LABELS = (LOW, EMERGING, NOTABLE, RESPECTED)

SEEN_WEIGHT = 1
ACQUAINTED_WEIGHT = 3
FAMILIAR_WEIGHT = 6
ELDER_INFLUENCE_BONUS = 2
RECENT_MEMORY_DAYS = 40
TOP_RELATIONSHIP_LIMIT = 5


def influence_score(agent: Agent, world: World | None = None) -> int:
    if world is None:
        return lifecycle_bonus(agent)

    key = villager_key(agent)
    incoming_scores = []
    for observer in world.living_agents():
        if observer is agent:
            continue

        entry = observer.social_memory.get(key)
        if entry is None:
            continue
        if not is_recent(entry.last_seen_day, world.day):
            continue

        score = familiarity_weight(entry.familiarity_score)
        if score > 0:
            incoming_scores.append(score)

    incoming_scores.sort(reverse=True)
    return sum(incoming_scores[:TOP_RELATIONSHIP_LIMIT]) + lifecycle_bonus(agent)


def influence_label(agent: Agent, world: World | None = None) -> str:
    return influence_label_for_score(influence_score(agent, world))


def peak_influence_label(agent: Agent) -> str:
    return influence_label_for_score(getattr(agent, "peak_influence_score", 0))


def update_agent_peak_influence(agent: Agent, world: World | None = None):
    current_score = influence_score(agent, world)
    agent.peak_influence_score = max(getattr(agent, "peak_influence_score", 0), current_score)


def update_influence_peaks(world: World):
    for agent in world.living_agents():
        update_agent_peak_influence(agent, world)


def influence_label_for_score(score: int) -> str:
    if score >= 24:
        return RESPECTED
    if score >= 12:
        return NOTABLE
    if score >= 4:
        return EMERGING
    return LOW


def familiarity_weight(score: int) -> int:
    level = familiarity_level(score)
    if level == FAMILIAR:
        return FAMILIAR_WEIGHT
    if level == ACQUAINTED:
        return ACQUAINTED_WEIGHT
    if level == SEEN:
        return SEEN_WEIGHT
    return 0


def lifecycle_bonus(agent: Agent) -> int:
    return ELDER_INFLUENCE_BONUS if getattr(agent, "lifecycle_stage", None) == ELDER else 0


def is_recent(last_seen_day: int, current_day: int) -> bool:
    return current_day - last_seen_day <= RECENT_MEMORY_DAYS
