from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.generations import SUCCESSION
from src.lifecycle import ADULT, ELDER, OLDER_ADULT, YOUNG_ADULT
from src.social_memory import villager_key

if TYPE_CHECKING:
    from src.agent import Agent
    from src.settlement import Household
    from src.world import World


SUCCESSION_ADULT_STAGES = {YOUNG_ADULT, ADULT, OLDER_ADULT, ELDER}


@dataclass(frozen=True)
class HouseholdSuccessionEvent:
    household_id: str
    old_head_id: str | None
    new_head_id: str | None
    reason: str


def handle_household_death_succession(world: World, deceased: Agent) -> HouseholdSuccessionEvent | None:
    household = world.household_for_agent(deceased) if hasattr(world, "household_for_agent") else None
    if household is None:
        return None

    deceased_id = villager_key(deceased)
    if household.household_head and household.household_head != deceased_id:
        return None

    successor = choose_household_successor(world, household, deceased)
    old_head = household.household_head
    new_head = villager_key(successor) if successor is not None else None
    household.household_head = new_head
    event = HouseholdSuccessionEvent(
        household_id=household.household_id,
        old_head_id=old_head,
        new_head_id=new_head,
        reason="head_death",
    )
    household.succession_history.append({
        "year": world.year,
        "day": world.day,
        "old_head_id": old_head,
        "new_head_id": new_head,
        "reason": event.reason,
    })
    household.succession_history = household.succession_history[-12:]
    world.household_succession_events_by_year = getattr(world, "household_succession_events_by_year", {})
    world.household_succession_events_by_year[world.year] = (
        world.household_succession_events_by_year.get(world.year, 0) + 1
    )
    record_household_succession_history(world, household, deceased, successor)
    return event


def choose_household_successor(world: World, household: Household, deceased: Agent) -> Agent | None:
    living = [
        agent
        for agent in world.living_agents()
        if getattr(agent, "household_id", None) == household.household_id and agent is not deceased
    ]
    if not living:
        return None

    partner_id = getattr(deceased, "partner_id", None)
    if partner_id:
        partner = next((agent for agent in living if villager_key(agent) == partner_id), None)
        if partner is not None and is_adult_successor(partner):
            return partner

    adult_children = [
        agent
        for agent in living
        if is_adult_successor(agent) and villager_key(agent) in set(getattr(deceased, "child_ids", []))
    ]
    if adult_children:
        return oldest_agent(adult_children)

    adults = [agent for agent in living if is_adult_successor(agent)]
    if adults:
        return oldest_agent(adults)

    return oldest_agent(living)


def is_adult_successor(agent: Agent) -> bool:
    return getattr(agent, "alive", False) and getattr(agent, "lifecycle_stage", None) in SUCCESSION_ADULT_STAGES


def oldest_agent(agents: list[Agent]) -> Agent | None:
    return max(agents, key=lambda agent: (getattr(agent, "age", 0), villager_key(agent)), default=None)


def record_household_succession_history(world: World, household: Household, deceased: Agent, successor: Agent | None) -> None:
    if successor is None:
        description = f"{household.household_name} lost its head, {deceased.name}, and has no adult successor."
    else:
        description = f"{successor.name} became head of {household.household_name} after {deceased.name} passed."

    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=SUCCESSION,
        title="Household Succession",
        description=description,
    )
