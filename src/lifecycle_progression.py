from __future__ import annotations

from dataclasses import dataclass

from src.config import ADULTHOOD_CHRONICLE_MIN_GENERATION, CHILD_ADULTHOOD_AGE, DAYS_PER_SEASON, SEASONS
from src.generations import FAMILY, MEMORY_CHILD, FamilyMemoryRecord
from src.lifecycle import CHILD, NOVICE, YOUNG_ADULT, lifecycle_stage_for_age
from src.roles import GENERALIST
from src.social_memory import villager_key


@dataclass(frozen=True)
class LifecycleTransition:
    villager_id: str
    name: str
    old_stage: str
    new_stage: str
    age: int


def update_lifecycle_progression(world) -> list[LifecycleTransition]:
    """Daily lifecycle pass: age villagers and transition children into the workforce."""
    transitions: list[LifecycleTransition] = []
    for agent in world.living_agents():
        previous_stage = getattr(agent, "lifecycle_stage", None)
        previous_age = getattr(agent, "age", 0)
        agent.age = current_age(world, agent)
        if previous_stage == CHILD and agent.age >= CHILD_ADULTHOOD_AGE:
            transitions.append(transition_child_to_adult(world, agent, previous_stage))
        elif previous_age != agent.age:
            agent.lifecycle_stage = lifecycle_stage_for_age(agent.age)
        agent.sync_generation_architecture()

    if transitions:
        world.adults_this_year = getattr(world, "adults_this_year", {})
        world.adults_this_year[world.year] = world.adults_this_year.get(world.year, 0) + len(transitions)
    return transitions


def current_age(world, agent) -> int:
    birth_year = getattr(agent, "birth_year", None)
    if birth_year is None:
        return max(0, int(getattr(agent, "age", 0)))

    birth_day = getattr(agent, "birth_day", None) or 1
    days_per_year = DAYS_PER_SEASON * len(SEASONS)
    absolute_birth_day = (birth_year - 1) * days_per_year + birth_day
    absolute_current_day = (world.year - 1) * days_per_year + world.day_of_year
    return max(0, (absolute_current_day - absolute_birth_day) // days_per_year)


def age_progress_to_next_year(world, agent) -> float:
    birth_year = getattr(agent, "birth_year", None)
    if birth_year is None:
        return 0.0
    birth_day = getattr(agent, "birth_day", None) or 1
    days_per_year = DAYS_PER_SEASON * len(SEASONS)
    absolute_birth_day = (birth_year - 1) * days_per_year + birth_day
    absolute_current_day = (world.year - 1) * days_per_year + world.day_of_year
    return ((absolute_current_day - absolute_birth_day) % days_per_year) / days_per_year


def days_until_adulthood(world, agent) -> int | None:
    if getattr(agent, "lifecycle_stage", None) != CHILD:
        return None
    birth_year = getattr(agent, "birth_year", None)
    if birth_year is None:
        remaining_years = max(0, CHILD_ADULTHOOD_AGE - int(getattr(agent, "age", 0)))
        return remaining_years * DAYS_PER_SEASON * len(SEASONS)
    birth_day = getattr(agent, "birth_day", None) or 1
    days_per_year = DAYS_PER_SEASON * len(SEASONS)
    adulthood_day = (birth_year - 1 + CHILD_ADULTHOOD_AGE) * days_per_year + birth_day
    current_day = (world.year - 1) * days_per_year + world.day_of_year
    return max(0, adulthood_day - current_day)


def transition_child_to_adult(world, agent, old_stage: str) -> LifecycleTransition:
    agent.lifecycle_stage = YOUNG_ADULT
    agent.current_goal = "Enter workforce"
    agent.current_action = "Joining workforce"
    agent.daily_role = None
    agent.task_state = "idle"
    if not agent.role:
        agent.role = GENERALIST
    if agent.experience_level == NOVICE:
        agent.experience_level = NOVICE

    transition = LifecycleTransition(
        villager_id=villager_key(agent),
        name=agent.name,
        old_stage=old_stage,
        new_stage=agent.lifecycle_stage,
        age=agent.age,
    )
    remember_adulthood(world, agent)
    record_adulthood_history(world, agent)
    return transition


def remember_adulthood(world, agent):
    memory = f"Reached adulthood and entered the workforce in Year {world.year}."
    if memory not in agent.personal_memories:
        agent.personal_memories.insert(0, memory)

    for parent in parent_agents(world, agent):
        parent_memory = f"{agent.name} reached adulthood in Year {world.year}."
        if parent_memory not in parent.personal_memories:
            parent.personal_memories.insert(0, parent_memory)
        parent.family_memories.append(FamilyMemoryRecord(
            category=MEMORY_CHILD,
            subject_id=villager_key(agent),
            description=parent_memory,
            year=world.year,
            day=world.day,
        ))


def parent_agents(world, agent):
    parent_ids = set(getattr(agent, "parent_ids", []) or [])
    for parent_id in (getattr(agent, "parent_a_id", None), getattr(agent, "parent_b_id", None)):
        if parent_id:
            parent_ids.add(parent_id)
    return [
        other
        for other in world.agents
        if (other.agent_id or other.name) in parent_ids
    ]


def record_adulthood_history(world, agent):
    if getattr(agent, "generation", 0) < ADULTHOOD_CHRONICLE_MIN_GENERATION:
        return
    history = getattr(world, "history", None)
    if history is None:
        return
    history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=FAMILY,
        title="Adulthood",
        description=f"{agent.name} reached adulthood and joined the village workforce.",
    )
