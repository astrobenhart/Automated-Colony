from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.generations import FAMILY, RELATIONSHIP_PARTNER
from src.lifecycle import ADULT, OLDER_ADULT, YOUNG_ADULT
from src.social_memory import SocialMemoryEntry, villager_key
from src.affection import clear_affection, reset_affection
from src.wanderers import is_active_wanderer

if TYPE_CHECKING:
    from src.agent import Agent
    from src.settlement import Household
    from src.world import World


PARTNERSHIP_MIN_SCORE = 45
PARTNERSHIP_DAILY_CHANCE = 0.35
MAX_NEW_PARTNERSHIPS_PER_DAY = 1
PARTNER_FAMILIARITY_FLOOR = 60
PARTNERSHIP_LIFE_STAGES = {YOUNG_ADULT, ADULT, OLDER_ADULT}


@dataclass(frozen=True)
class PartnershipCandidate:
    first: Agent
    second: Agent
    score: int


def update_partnerships(world: World) -> list[tuple[Agent, Agent]]:
    """Run the infrequent social pass that establishes enduring pair bonds."""
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return []

    refresh_partnership_durations(world)
    rng = random.Random(f"{getattr(world, 'seed', None)}|partnerships|{world.day}")
    if rng.random() > PARTNERSHIP_DAILY_CHANCE:
        return []

    candidates = partnership_candidates(world)
    if not candidates:
        return []

    rng.shuffle(candidates)
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)

    formed: list[tuple[Agent, Agent]] = []
    paired_ids: set[str] = set()
    for candidate in candidates:
        if len(formed) >= MAX_NEW_PARTNERSHIPS_PER_DAY:
            break
        first_id = villager_key(candidate.first)
        second_id = villager_key(candidate.second)
        if first_id in paired_ids or second_id in paired_ids:
            continue
        if not partnership_eligible(candidate.first, candidate.second, world):
            continue
        formed.append(form_partnership(world, candidate.first, candidate.second))
        paired_ids.update({first_id, second_id})

    return formed


def partnership_candidates(world: World) -> list[PartnershipCandidate]:
    agents = [
        agent
        for agent in world.living_agents()
        if is_unpartnered_adult(agent)
    ]
    candidates: list[PartnershipCandidate] = []
    for index, first in enumerate(agents):
        for second in agents[index + 1:]:
            if not partnership_eligible(first, second, world):
                continue
            score = partnership_score(first, second, world)
            if score >= PARTNERSHIP_MIN_SCORE:
                candidates.append(PartnershipCandidate(first, second, score))
    return candidates


def partnership_eligible(first: Agent, second: Agent, world: World) -> bool:
    if first is second:
        return False
    if not is_unpartnered_adult(first) or not is_unpartnered_adult(second):
        return False
    if settlement_id_for(first) != settlement_id_for(second):
        return False
    if settlement_id_for(first) is None:
        return False
    if are_direct_family(first, second):
        return False
    return True


def is_unpartnered_adult(agent: Agent) -> bool:
    return (
        getattr(agent, "alive", False)
        and not is_active_wanderer(agent)
        and getattr(agent, "partner_id", None) is None
        and not getattr(agent, "partner_ids", [])
        and getattr(agent, "lifecycle_stage", None) in PARTNERSHIP_LIFE_STAGES
    )


def settlement_id_for(agent: Agent) -> str | None:
    return getattr(agent, "home_settlement_id", None) or getattr(agent, "birth_settlement_id", None)


def are_direct_family(first: Agent, second: Agent) -> bool:
    first_id = villager_key(first)
    second_id = villager_key(second)
    first_family = set(getattr(first, "parent_ids", []))
    first_family.update(getattr(first, "child_ids", []))
    first_family.update(getattr(first, "children_ids", []))
    first_family.update(getattr(first, "sibling_ids", []))
    second_family = set(getattr(second, "parent_ids", []))
    second_family.update(getattr(second, "child_ids", []))
    second_family.update(getattr(second, "children_ids", []))
    second_family.update(getattr(second, "sibling_ids", []))
    return second_id in first_family or first_id in second_family


def partnership_score(first: Agent, second: Agent, world: World) -> int:
    first_score = memory_score(first, second)
    second_score = memory_score(second, first)
    score = (first_score + second_score) // 2

    first_household = world.household_for_agent(first) if hasattr(world, "household_for_agent") else None
    second_household = world.household_for_agent(second) if hasattr(world, "household_for_agent") else None
    if first_household is not None and first_household is second_household:
        score += min(12, max(0, getattr(first_household, "established_years", 0) // 2))
    if getattr(first, "workplace_id", None) and getattr(first, "workplace_id", None) == getattr(second, "workplace_id", None):
        score += 6
    return score


def memory_score(observer: Agent, other: Agent) -> int:
    entry = getattr(observer, "social_memory", {}).get(villager_key(other))
    if entry is None:
        return 0
    return entry.familiarity_score


def form_partnership(world: World, first: Agent, second: Agent) -> tuple[Agent, Agent]:
    first_id = villager_key(first)
    second_id = villager_key(second)

    first.partner_id = second_id
    second.partner_id = first_id
    first.partner_ids = [second_id]
    second.partner_ids = [first_id]
    first.partnership_start_year = world.year
    second.partnership_start_year = world.year
    first.partnership_duration = 0
    second.partnership_duration = 0
    reset_affection(first, second)
    first.sync_generation_architecture()
    second.sync_generation_architecture()

    mark_partner_relationship(first, second, world.day)
    mark_partner_relationship(second, first, world.day)
    add_partnership_memory(first, second, world)
    add_partnership_memory(second, first, world)

    moved = prefer_shared_household(world, first, second)
    record_partnership_history(world, first, second, moved)
    return first, second


def end_partnership_due_to_death(world: World, deceased: Agent) -> None:
    """Clear active partner references when death naturally ends a partnership."""
    deceased_id = villager_key(deceased)
    partner_id = getattr(deceased, "partner_id", None)
    if not partner_id:
        return

    survivor = next(
        (agent for agent in world.living_agents() if villager_key(agent) == partner_id),
        None,
    )
    if survivor is not None and getattr(survivor, "partner_id", None) == deceased_id:
        survivor.partner_id = None
        survivor.partner_ids = [pid for pid in getattr(survivor, "partner_ids", []) if pid != deceased_id]
        survivor.partnership_start_year = None
        survivor.partnership_duration = 0
        clear_affection(survivor)
        memories = getattr(survivor, "personal_memories", None)
        if memories is not None:
            memory = f"Lost long-term partner {getattr(deceased, 'name', 'a partner')} in Year {world.year}."
            if memory not in memories:
                memories.insert(0, memory)
        survivor.sync_generation_architecture()

    deceased.partner_id = None
    deceased.partner_ids = [pid for pid in getattr(deceased, "partner_ids", []) if pid != partner_id]
    deceased.partnership_start_year = None
    deceased.partnership_duration = 0
    clear_affection(deceased)
    deceased.sync_generation_architecture()


def refresh_partnership_durations(world: World):
    for agent in world.living_agents():
        start_year = getattr(agent, "partnership_start_year", None)
        if getattr(agent, "partner_id", None) is None or start_year is None:
            continue
        agent.partnership_duration = max(0, world.year - start_year)
        agent.sync_generation_architecture()


def mark_partner_relationship(observer: Agent, partner: Agent, day: int):
    key = villager_key(partner)
    entry = observer.social_memory.get(key)
    if entry is None:
        entry = SocialMemoryEntry(
            villager_id=key,
            display_name=partner.name,
            last_seen_day=day,
        )
        observer.social_memory[key] = entry
    entry.display_name = partner.name
    entry.last_seen_day = day
    entry.familiarity_score = max(entry.familiarity_score, PARTNER_FAMILIARITY_FLOOR)
    relationship_types = list(entry.relationship_types or [])
    if RELATIONSHIP_PARTNER not in relationship_types:
        relationship_types.append(RELATIONSHIP_PARTNER)
    entry.relationship_types = relationship_types


def add_partnership_memory(agent: Agent, partner: Agent, world: World):
    memory = f"Formed a long-term partnership with {partner.name} in Year {world.year}."
    memories = getattr(agent, "personal_memories", None)
    if memories is not None and memory not in memories:
        memories.insert(0, memory)


def add_household_memory(agent: Agent, household: Household, world: World):
    memory = f"Joined {household.household_name} with a partner in Year {world.year}."
    memories = getattr(agent, "personal_memories", None)
    if memories is not None and memory not in memories:
        memories.insert(0, memory)


def prefer_shared_household(world: World, first: Agent, second: Agent) -> bool:
    first_household = world.household_for_agent(first) if hasattr(world, "household_for_agent") else None
    second_household = world.household_for_agent(second) if hasattr(world, "household_for_agent") else None
    if first_household is None and second_household is None:
        return False
    if first_household is second_household:
        return False
    if first_household is None:
        world.add_agent_to_household(first, second_household)
        add_household_memory(first, second_household, world)
        return True
    if second_household is None:
        world.add_agent_to_household(second, first_household)
        add_household_memory(second, first_household, world)
        return True

    if first_household.size <= 1:
        world.add_agent_to_household(first, second_household)
        add_household_memory(first, second_household, world)
        return True
    if second_household.size <= 1:
        world.add_agent_to_household(second, first_household)
        add_household_memory(second, first_household, world)
        return True
    household = create_partner_household(world, first, second, first_household)
    if household is not None:
        world.add_agent_to_household(first, household)
        world.add_agent_to_household(second, household)
        add_household_memory(first, household, world)
        add_household_memory(second, household, world)
        return True
    return False


def create_partner_household(world: World, first: Agent, second: Agent, source_household: Household | None) -> Household | None:
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return None
    household_id = next_household_id(settlement)
    household = type(source_household)(
        household_id=household_id,
        household_name=partner_household_name(settlement, first, second),
        home_id=None,
        home_building_id=None,
        member_ids=[],
        founder_ids=[villager_key(first), villager_key(second)],
        founded_year=world.year,
        household_head=villager_key(first),
    )
    settlement.households.append(household)
    return household


def next_household_id(settlement) -> str:
    existing = {household.household_id for household in settlement.households}
    index = len(existing)
    while f"household-{index}" in existing:
        index += 1
    return f"household-{index}"


def partner_household_name(settlement, first: Agent, second: Agent) -> str:
    base = f"{getattr(first, 'name', 'New')} {getattr(second, 'name', 'Hearth')}"
    existing = {household.household_name for household in settlement.households}
    name = f"{base} Hearth"
    if name not in existing:
        return name
    index = 2
    while f"{base} Hearth {index}" in existing:
        index += 1
    return f"{base} Hearth {index}"


def record_partnership_history(world: World, first: Agent, second: Agent, moved_household: bool):
    history = getattr(world, "history", None)
    if history is None:
        return
    if moved_household:
        title = "Household Partnership"
        description = f"{first.name} and {second.name} formed a long-term partnership and began sharing a household."
    else:
        title = "Long-Term Partnership"
        description = f"{first.name} and {second.name} formed a long-term partnership."
    history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=FAMILY,
        title=title,
        description=description,
    )
