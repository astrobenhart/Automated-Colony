from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.friendships import close_friend_ids
from src.gatherings import GATHERING_RADIUS, gathering_participant
from src.social_memory import chebyshev_distance, villager_key
from src.world_history import LOCAL_STORY

if TYPE_CHECKING:
    from src.agent import Agent
    from src.death_memory import DeathRecord
    from src.world import World


OPEN_CREMATION = "Open Cremation"
OPEN_CREMATION_DURATION_DAYS = 3


@dataclass(frozen=True)
class ActiveCelebration:
    celebration_type: str
    title: str
    description: str
    anchor: tuple[int, int]
    started_day: int
    duration_days: int
    honoree_id: str | None = None
    honoree_name: str | None = None


def update_celebrations(world: World):
    if active_celebration(world) is None:
        world.active_celebration = None


def active_celebration(world: World) -> ActiveCelebration | None:
    celebration = getattr(world, "active_celebration", None)
    if celebration is None:
        return None
    if world.day >= celebration.started_day + celebration.duration_days:
        return None
    return celebration


def maybe_start_open_cremation(world: World, deceased: Agent, record: DeathRecord) -> ActiveCelebration | None:
    if getattr(world, "settlement", None) is None:
        return None
    if not should_hold_open_cremation(record):
        return None

    anchor = choose_open_cremation_site(world, record)
    if anchor is None:
        return None

    settlement_name = getattr(world.settlement, "name", "the village")
    celebration = ActiveCelebration(
        celebration_type=OPEN_CREMATION,
        title=f"{record.name}'s Funeral Fire",
        description=f"A funeral fire was lit for {record.name} outside {settlement_name}.",
        anchor=anchor,
        started_day=world.day,
        duration_days=OPEN_CREMATION_DURATION_DAYS,
        honoree_id=record.villager_id,
        honoree_name=record.name,
    )
    world.active_celebration = celebration
    world.celebration_history.append(celebration)
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title="Open Cremation",
        description=celebration.description,
    )
    return celebration


def should_hold_open_cremation(record: DeathRecord) -> bool:
    if record.peak_influence_label in {"Notable", "Respected"}:
        return True
    if len(record.remembered_by) >= 2:
        return True
    return record.lifecycle_stage == "Elder" and record.cause_of_death == "old age"


def choose_open_cremation_site(world: World, record: DeathRecord) -> tuple[int, int] | None:
    settlement = world.settlement
    if settlement is None:
        return None

    rng = random.Random(f"{world.seed}|{record.villager_id}|{world.day}|open-cremation")
    candidates = []
    min_distance = min(max(4, settlement.radius + 2), max(world.width, world.height))
    max_distance = min(max(6, settlement.radius + 6), max(world.width, world.height))
    for y in range(world.height):
        for x in range(world.width):
            if not world.is_valid_spawn_tile(x, y):
                continue
            distance = chebyshev_distance(x, y, settlement.x, settlement.y)
            if min_distance <= distance <= max_distance:
                candidates.append((abs(distance - min_distance), rng.random(), (x, y)))

    if not candidates:
        for y in range(world.height):
            for x in range(world.width):
                if world.is_valid_spawn_tile(x, y):
                    distance = chebyshev_distance(x, y, settlement.x, settlement.y)
                    candidates.append((-distance, rng.random(), (x, y)))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def celebration_destination(world: World) -> tuple[str, tuple[int, int]] | None:
    celebration = active_celebration(world)
    if celebration is None:
        return None
    return f"Ceremony: {celebration.celebration_type}", celebration.anchor


def celebration_attraction(agent: Agent, world: World) -> float:
    celebration = active_celebration(world)
    if celebration is None:
        return 0.0
    score = 32.0
    honoree_id = celebration.honoree_id
    if honoree_id:
        if getattr(agent, "remembering", None) == celebration.honoree_name:
            score += 24
        if getattr(agent, "partner_id", None) == honoree_id:
            score += 35
        if honoree_id in getattr(agent, "parent_ids", []):
            score += 30
        if honoree_id in getattr(agent, "child_ids", []) or honoree_id in getattr(agent, "children_ids", []):
            score += 24
        if honoree_id in close_friend_ids(agent):
            score += 26
        if same_household_as_honoree(agent, world, honoree_id):
            score += 22
        if same_family_as_honoree(agent, world, honoree_id):
            score += 16
    return score


def same_household_as_honoree(agent: Agent, world: World, honoree_id: str) -> bool:
    household_id = getattr(agent, "household_id", None)
    if not household_id or getattr(world, "settlement", None) is None:
        return False
    household = world.settlement.household_for(household_id)
    return household is not None and honoree_id in household.historical_member_ids


def same_family_as_honoree(agent: Agent, world: World, honoree_id: str) -> bool:
    family_id = getattr(agent, "family_id", None)
    if not family_id:
        return False
    family = getattr(world, "families", {}).get(family_id)
    if family is None:
        return False
    return honoree_id in getattr(family, "living_member_ids", set()) or honoree_id in getattr(family, "deceased_member_ids", set())


def celebration_attendees(world: World) -> list[Agent]:
    celebration = active_celebration(world)
    if celebration is None:
        return []
    attendees = [
        agent
        for agent in world.living_agents()
        if gathering_participant(agent)
        and chebyshev_distance(agent.x, agent.y, celebration.anchor[0], celebration.anchor[1]) <= GATHERING_RADIUS
    ]
    attendees.sort(key=lambda agent: agent.name)
    return attendees


def ceremony_status(agent: Agent, world: World | None = None) -> tuple[str, str]:
    if world is None:
        return "None", "Not Attending"
    celebration = active_celebration(world)
    if celebration is None:
        return "None", "Not Attending"
    if not gathering_participant(agent):
        return celebration.title, "Not Attending"
    distance = chebyshev_distance(agent.x, agent.y, celebration.anchor[0], celebration.anchor[1])
    if distance <= GATHERING_RADIUS:
        return celebration.title, "Attending"
    return celebration.title, "Not Attending"


def celebration_diagnostics(world: World) -> list[tuple[str, object]]:
    celebration = active_celebration(world)
    attendees = celebration_attendees(world)
    history = getattr(world, "celebration_history", [])
    attendance_counts = [
        len([
            agent
            for agent in world.living_agents()
            if chebyshev_distance(agent.x, agent.y, item.anchor[0], item.anchor[1]) <= GATHERING_RADIUS
        ])
        for item in history
    ]
    return [
        ("Active Celebration", celebration.title if celebration is not None else "None"),
        ("Villagers Attending", len(attendees)),
        ("Average Attendance", f"{(sum(attendance_counts) / len(attendance_counts)):.1f}" if attendance_counts else "0.0"),
        ("Celebration History", len(history)),
    ]
