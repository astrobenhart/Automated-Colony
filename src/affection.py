from __future__ import annotations

from typing import TYPE_CHECKING

from src.social_memory import chebyshev_distance, villager_key
from src.world_history import LOCAL_STORY

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


AFFECTION_ESTABLISHED_THRESHOLD = 30
AFFECTION_STRONG_THRESHOLD = 75
AFFECTION_LIFELONG_THRESHOLD = 130
AFFECTION_MAX_SCORE = 240
AFFECTION_CHRONICLE_LIMIT_PER_YEAR = 2
PARTNER_PROXIMITY_RADIUS = 2
RELATIONSHIP_GRIEF_BY_LABEL = {
    "Established": (6, 5),
    "Strong": (8, 7),
    "Lifelong": (12, 10),
}
RELATIONSHIP_RECOVERY_DAYS = 8


def update_affection(world: World):
    """Deepen existing partnerships from ordinary shared life."""
    for first, second in active_partnership_pairs(world):
        amount = daily_affection_gain(world, first, second)
        if amount <= 0:
            continue
        previous_label = affection_label(first)
        add_affection(first, second, amount)
        maybe_record_affection_milestone(world, first, second, previous_label)


def active_partnership_pairs(world: World) -> list[tuple[Agent, Agent]]:
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    seen: set[frozenset[str]] = set()
    pairs: list[tuple[Agent, Agent]] = []
    for first in living_by_id.values():
        second_id = getattr(first, "partner_id", None)
        if not second_id or second_id not in living_by_id:
            continue
        second = living_by_id[second_id]
        if getattr(second, "partner_id", None) != villager_key(first):
            continue
        pair_key = frozenset((villager_key(first), villager_key(second)))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        pairs.append((first, second))
    return pairs


def daily_affection_gain(world: World, first: Agent, second: Agent) -> int:
    gain = 0
    if same_household(first, second):
        gain += 1
    if shared_moment_together(first, second, world):
        gain += 2
    elif spending_free_time_together(first, second):
        gain += 1
    if attending_same_celebration(first, second, world):
        gain += 1
    if raising_children_together(world, first, second):
        gain += 1
    if working_together(first, second):
        gain += 1
    if enduring_hardship_together(first, second):
        gain += 1
    return min(gain, 5)


def add_affection(first: Agent, second: Agent, amount: int):
    next_score = min(
        AFFECTION_MAX_SCORE,
        max(getattr(first, "partner_affection", 0), getattr(second, "partner_affection", 0)) + amount,
    )
    first.partner_affection = next_score
    second.partner_affection = next_score


def reset_affection(first: Agent, second: Agent):
    first.partner_affection = 0
    second.partner_affection = 0
    first.partner_affection_recorded_levels = []
    second.partner_affection_recorded_levels = []


def clear_affection(agent: Agent):
    agent.partner_affection = 0
    agent.partner_affection_recorded_levels = []


def affection_label(agent: Agent) -> str:
    score = getattr(agent, "partner_affection", 0)
    if score >= AFFECTION_LIFELONG_THRESHOLD:
        return "Lifelong"
    if score >= AFFECTION_STRONG_THRESHOLD:
        return "Strong"
    if score >= AFFECTION_ESTABLISHED_THRESHOLD:
        return "Established"
    return "Growing"


def affection_mood_bonus(agent: Agent, world: World) -> int:
    return relationship_positive_mood_bonus(agent, world)


def relationship_positive_mood_bonus(agent: Agent, world: World) -> int:
    partner = active_partner(agent, world)
    if partner is None:
        return 0
    label = affection_label(agent)
    if label == "Growing":
        return 0
    bonus = 0
    if same_household(agent, partner):
        bonus += 1
    if spending_free_time_together(agent, partner):
        bonus += 1
    if shared_moment_together(agent, partner, world):
        bonus += 2
    if attending_same_celebration(agent, partner, world):
        bonus += 1
    if raising_children_together(world, agent, partner):
        bonus += 1
    if label == "Lifelong":
        bonus += 1
    return min(4, bonus)


def relationship_grief_penalty(agent: Agent, world: World) -> int:
    grief_until = getattr(agent, "relationship_grief_until_day", 0)
    recovery_until = getattr(agent, "relationship_recovery_until_day", 0)
    penalty = getattr(agent, "relationship_grief_penalty", 0)
    if grief_until and world.day < grief_until:
        return max(0, penalty)
    if recovery_until and world.day < recovery_until:
        return max(1, penalty // 3)
    return 0


def relationship_mood_label(agent: Agent, world: World | None = None) -> str:
    if world is not None:
        grief_until = getattr(agent, "relationship_grief_until_day", 0)
        recovery_until = getattr(agent, "relationship_recovery_until_day", 0)
        if grief_until and world.day < grief_until:
            return "Grieving"
        if recovery_until and world.day < recovery_until:
            return "Recovering"
        if relationship_positive_mood_bonus(agent, world) >= 3:
            return "Happy"
    return "Content"


def has_nearby_partner(agent: Agent, world: World) -> bool:
    partner = active_partner(agent, world)
    return partner is not None and near_each_other(agent, partner)


def partner_nearby_label(agent: Agent, world: World | None) -> str:
    if world is None:
        return "Unknown"
    return "Yes" if has_nearby_partner(agent, world) else "No"


def active_partner(agent: Agent, world: World) -> Agent | None:
    partner_id = getattr(agent, "partner_id", None)
    if not partner_id:
        return None
    for other in world.living_agents():
        if villager_key(other) == partner_id and getattr(other, "partner_id", None) == villager_key(agent):
            return other
    return None


def same_household(first: Agent, second: Agent) -> bool:
    household_id = getattr(first, "household_id", None)
    return bool(household_id and household_id == getattr(second, "household_id", None))


def near_each_other(first: Agent, second: Agent) -> bool:
    return chebyshev_distance(first.x, first.y, second.x, second.y) <= PARTNER_PROXIMITY_RADIUS


def spending_free_time_together(first: Agent, second: Agent) -> bool:
    from src.gatherings import gathering_participant

    return gathering_participant(first) and gathering_participant(second) and near_each_other(first, second)


def shared_moment_together(first: Agent, second: Agent, world: World) -> bool:
    from src.shared_moments import current_shared_moment

    first_moment = current_shared_moment(first, world)
    return bool(first_moment and first_moment == current_shared_moment(second, world) and near_each_other(first, second))


def attending_same_celebration(first: Agent, second: Agent, world: World) -> bool:
    from src.celebrations import active_celebration

    celebration = active_celebration(world)
    if celebration is None:
        return False
    anchor = celebration.anchor
    return (
        chebyshev_distance(first.x, first.y, anchor[0], anchor[1]) <= PARTNER_PROXIMITY_RADIUS
        and chebyshev_distance(second.x, second.y, anchor[0], anchor[1]) <= PARTNER_PROXIMITY_RADIUS
    )


def raising_children_together(world: World, first: Agent, second: Agent) -> bool:
    parent_ids = {villager_key(first), villager_key(second)}
    for child in world.living_agents():
        if parent_ids <= set(getattr(child, "parent_ids", []) or []):
            return True
    return False


def working_together(first: Agent, second: Agent) -> bool:
    first_action = getattr(first, "current_action", None)
    second_action = getattr(second, "current_action", None)
    working_actions = {"Building", "Harvesting", "Harvesting farm", "Planting", "Depositing", "Gathering wood"}
    if first_action != second_action or first_action not in working_actions:
        return False
    if getattr(first, "workplace_id", None) and getattr(first, "workplace_id", None) == getattr(second, "workplace_id", None):
        return True
    return getattr(first, "task_target", None) is not None and getattr(first, "task_target", None) == getattr(second, "task_target", None)


def enduring_hardship_together(first: Agent, second: Agent) -> bool:
    if not same_household(first, second):
        return False
    for need in ("hunger", "thirst", "fatigue"):
        if getattr(first, need, 0) >= 65 and getattr(second, need, 0) >= 45:
            return True
        if getattr(second, need, 0) >= 65 and getattr(first, need, 0) >= 45:
            return True
    return False


def maybe_record_affection_milestone(world: World, first: Agent, second: Agent, previous_label: str):
    label = affection_label(first)
    if label == previous_label or label not in {"Strong", "Lifelong"}:
        return
    if not mark_affection_level_recorded(first, second, label):
        return
    if affection_chronicle_count_this_year(world) >= AFFECTION_CHRONICLE_LIMIT_PER_YEAR:
        return
    key = affection_pair_key(first, second, label)
    keys = getattr(world, "affection_chronicle_keys", None)
    if keys is None:
        world.affection_chronicle_keys = set()
        keys = world.affection_chronicle_keys
    if key in keys:
        return
    keys.add(key)
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title=f"{label} Partnership",
        description=affection_chronicle_description(first, second, label),
    )


def mark_affection_level_recorded(first: Agent, second: Agent, label: str) -> bool:
    recorded = set(getattr(first, "partner_affection_recorded_levels", []) or [])
    if label in recorded:
        return False
    for agent in (first, second):
        levels = list(getattr(agent, "partner_affection_recorded_levels", []) or [])
        if label not in levels:
            levels.append(label)
        agent.partner_affection_recorded_levels = levels
    return True


def affection_pair_key(first: Agent, second: Agent, label: str) -> str:
    pair = "-".join(sorted((villager_key(first), villager_key(second))))
    return f"{pair}:{label}"


def affection_chronicle_description(first: Agent, second: Agent, label: str) -> str:
    if label == "Lifelong":
        return f"{first.name} and {second.name} had built one of the village's lifelong partnerships and were rarely seen apart."
    return f"{first.name} and {second.name} had grown into a strong partnership over years of shared life."


def partners_spending_free_time_together(world: World) -> int:
    return sum(1 for first, second in active_partnership_pairs(world) if spending_free_time_together(first, second))


def average_partnered_gathering_participation(world: World) -> str:
    pairs = active_partnership_pairs(world)
    if not pairs:
        return "0.0%"
    from src.gatherings import gathering_participant

    participating = sum(1 for first, second in pairs if gathering_participant(first) or gathering_participant(second))
    return f"{(participating / len(pairs) * 100):.1f}%"


def affection_chronicle_count_this_year(world: World) -> int:
    return sum(
        1
        for entry in getattr(world.history, "entries", [])
        if entry.year == world.year and entry.category == LOCAL_STORY and entry.title in {"Strong Partnership", "Lifelong Partnership", "Partner Mourned"}
    )


def handle_partner_death(world: World, deceased: Agent):
    survivor = active_partner_for_deceased(world, deceased)
    if survivor is None:
        return
    label = affection_label(survivor)
    if label == "Growing":
        return
    duration, penalty = RELATIONSHIP_GRIEF_BY_LABEL.get(label, RELATIONSHIP_GRIEF_BY_LABEL["Established"])
    survivor.remembering = deceased.name
    survivor.remembrance_expires_day = max(getattr(survivor, "remembrance_expires_day", 0), world.day + duration)
    survivor.relationship_grief_until_day = max(getattr(survivor, "relationship_grief_until_day", 0), world.day + duration)
    survivor.relationship_recovery_until_day = max(
        getattr(survivor, "relationship_recovery_until_day", 0),
        world.day + duration + RELATIONSHIP_RECOVERY_DAYS,
    )
    survivor.relationship_grief_penalty = max(getattr(survivor, "relationship_grief_penalty", 0), penalty)
    memory = f"Mourned {label.lower()} partner {deceased.name} in Year {world.year}."
    if memory not in survivor.personal_memories:
        survivor.personal_memories.insert(0, memory)
    if label in {"Strong", "Lifelong"}:
        record_partner_mourning_chronicle(world, survivor, deceased, label)


def active_partner_for_deceased(world: World, deceased: Agent) -> Agent | None:
    deceased_id = villager_key(deceased)
    partner_id = getattr(deceased, "partner_id", None)
    if not partner_id:
        return None
    for agent in world.living_agents():
        if villager_key(agent) == partner_id and getattr(agent, "partner_id", None) == deceased_id:
            return agent
    return None


def record_partner_mourning_chronicle(world: World, survivor: Agent, deceased: Agent, label: str):
    if affection_chronicle_count_this_year(world) >= AFFECTION_CHRONICLE_LIMIT_PER_YEAR:
        return
    key = f"mourning:{villager_key(survivor)}:{villager_key(deceased)}:{world.year}"
    keys = getattr(world, "affection_chronicle_keys", None)
    if keys is None:
        world.affection_chronicle_keys = set()
        keys = world.affection_chronicle_keys
    if key in keys:
        return
    keys.add(key)
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title="Partner Mourned",
        description=f"{survivor.name} mourned the loss of {label.lower()} partner {deceased.name}.",
    )
