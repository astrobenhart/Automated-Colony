from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING

from src.lifecycle import EXPERIENCED, VETERAN
from src.social_memory import SocialMemoryEntry, villager_key
from src.workplace import FARM, STORAGE, VILLAGE_CENTER, WORKSHOP

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


MAX_STARTING_MEMORIES = 4


def seed_preexisting_social_history(world: World):
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return

    agents = world.living_agents()
    if not agents:
        return

    agents_by_id = {villager_key(agent): agent for agent in agents}
    seed_role_and_routine_history(world, agents)
    seed_household_relationships(world, agents_by_id)
    seed_workplace_relationships(world, agents_by_id)
    seed_role_relationships(world, agents)


def seed_role_and_routine_history(world: World, agents: list[Agent]):
    for agent in agents:
        rng = random.Random(f"{world.seed}|{villager_key(agent)}|role-history")
        working_years = max(0, getattr(agent, "age", 18) - 18)
        agent.years_in_role = role_years_for(agent, working_years, rng)
        agent.routine_age = routine_years_for(agent, working_years, rng)
        agent.workplace_familiarity = min(agent.years_in_role, agent.routine_age)
        agent.personal_memories = role_memory_lines(agent)


def role_years_for(agent: Agent, working_years: int, rng: random.Random) -> int:
    if working_years <= 0:
        return 0
    experience = getattr(agent, "experience_level", None)
    if experience == VETERAN:
        low, high = 7, min(working_years, 22)
    elif experience == EXPERIENCED:
        low, high = 2, min(working_years, 10)
    else:
        low, high = 0, min(working_years, 3)
    if high < low:
        low = 0
    return rng.randint(low, max(low, high))


def routine_years_for(agent: Agent, working_years: int, rng: random.Random) -> int:
    if working_years <= 0:
        return 0
    role_years = getattr(agent, "years_in_role", 0)
    household_years = getattr(agent, "household_familiarity", 0)
    upper = max(1, min(working_years, max(role_years, household_years, 1) + 3))
    return rng.randint(1, upper)


def role_memory_lines(agent: Agent) -> list[str]:
    memories = []
    years = getattr(agent, "years_in_role", 0)
    if years > 0:
        memories.append(f"Worked as {agent.role} for {years} years.")
    if getattr(agent, "workplace_id", None):
        memories.append(f"Kept a steady routine at {agent.workplace_id}.")
    if getattr(agent, "routine_age", 0) >= 3:
        memories.append(f"Followed the same village routines for {agent.routine_age} years.")
    return memories[:MAX_STARTING_MEMORIES]


def seed_household_relationships(world: World, agents_by_id: dict[str, Agent]):
    settlement = world.settlement
    for household in settlement.households:
        members = [
            agents_by_id[member_id]
            for member_id in household.member_ids
            if member_id in agents_by_id
        ]
        if not members:
            continue

        years = max(0, household.established_years)
        for member in members:
            member.household_familiarity = years
            add_memory(member, f"Shared {household.household_name} for {years} years.")

        score = household_score(years)
        for observer in members:
            for other in members:
                if observer is other:
                    continue
                seed_relationship(observer, other, score, world.day)


def seed_workplace_relationships(world: World, agents_by_id: dict[str, Agent]):
    settlement = world.settlement
    for workplace in settlement.workplaces:
        workers = [
            agents_by_id[worker_id]
            for worker_id in workplace.assigned_workers
            if worker_id in agents_by_id
        ]
        if len(workers) < 2:
            continue

        for worker in workers:
            worker.workplace_familiarity = max(worker.workplace_familiarity, getattr(worker, "years_in_role", 0))
            add_memory(worker, workplace_memory_line(workplace.workplace_type, worker.workplace_familiarity))

        for observer in workers:
            for other in workers:
                if observer is other:
                    continue
                years = min(observer.workplace_familiarity, other.workplace_familiarity)
                seed_relationship(observer, other, workplace_score(years), world.day)


def seed_role_relationships(world: World, agents: list[Agent]):
    by_role: dict[str, list[Agent]] = defaultdict(list)
    for agent in agents:
        by_role[getattr(agent, "role", "Unknown")].append(agent)

    for role, peers in by_role.items():
        if len(peers) < 2:
            continue
        peers.sort(key=lambda agent: (-(getattr(agent, "years_in_role", 0)), villager_key(agent)))
        for observer in peers:
            for other in peers[:3]:
                if observer is other:
                    continue
                years = min(observer.years_in_role, other.years_in_role)
                seed_relationship(observer, other, role_peer_score(years), world.day)
            if observer.years_in_role >= 3:
                add_memory(observer, f"Worked alongside other {role} villagers for years.")


def household_score(years: int) -> int:
    return min(55, 4 + max(0, years) * 3)


def workplace_score(years: int) -> int:
    return min(36, 4 + max(0, years) * 2)


def role_peer_score(years: int) -> int:
    return min(18, 2 + max(0, years))


def seed_relationship(observer: Agent, other: Agent, score: int, day: int):
    if score <= 0:
        return
    key = villager_key(other)
    entry = observer.social_memory.get(key)
    if entry is None:
        observer.social_memory[key] = SocialMemoryEntry(
            villager_id=key,
            display_name=other.name,
            familiarity_score=score,
            last_seen_day=day,
        )
        return

    entry.display_name = other.name
    entry.familiarity_score = max(entry.familiarity_score, score)
    entry.last_seen_day = max(entry.last_seen_day, day)


def workplace_memory_line(workplace_type: str, years: int) -> str:
    label = {
        FARM: "farm area",
        STORAGE: "storage area",
        WORKSHOP: "workshop",
        VILLAGE_CENTER: "village center",
    }.get(workplace_type, "workplace")
    if years > 0:
        return f"Worked around the {label} for {years} years."
    return f"Worked around the {label}."


def add_memory(agent: Agent, text: str):
    memories = getattr(agent, "personal_memories", None)
    if memories is None:
        agent.personal_memories = []
        memories = agent.personal_memories
    if text and text not in memories and len(memories) < MAX_STARTING_MEMORIES:
        memories.append(text)
