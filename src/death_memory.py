from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.influence import influence_label, peak_influence_label
from src.social_memory import FAMILIAR, familiarity_level, villager_key
from src.world_history import DEATH

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


REMEMBRANCE_DURATION_DAYS = 4


@dataclass(frozen=True)
class DeathRecord:
    name: str
    villager_id: str
    role: str | None
    lifecycle_stage: str | None
    trait: str | None
    appearance_seed: int | None
    appearance_type: str | None
    influence_label: str
    peak_influence_label: str
    cause_of_death: str
    day: int
    season: str
    year: int
    remembered_by: list[str] = field(default_factory=list)


def record_death(world: World, agent: Agent, cause_of_death: str) -> DeathRecord:
    villager_id = villager_key(agent)
    existing = death_record_for(world, villager_id)
    if existing is not None:
        return existing

    remembered_by = remembered_villagers(world, agent)
    record = DeathRecord(
        name=getattr(agent, "name", "Villager"),
        villager_id=villager_id,
        role=getattr(agent, "role", None),
        lifecycle_stage=getattr(agent, "lifecycle_stage", None),
        trait=getattr(agent, "trait", None),
        appearance_seed=getattr(agent, "appearance_seed", None),
        appearance_type=getattr(agent, "appearance_type", None),
        influence_label=influence_label(agent, world),
        peak_influence_label=peak_influence_label(agent),
        cause_of_death=cause_of_death,
        day=world.day,
        season=world.season,
        year=world.year,
        remembered_by=remembered_by,
    )
    world.death_records.append(record)
    create_remembrance(world, agent, remembered_by)
    record_death_history(world, record)
    return record


def death_record_for(world: World, villager_id: str) -> DeathRecord | None:
    for record in world.death_records:
        if record.villager_id == villager_id:
            return record
    return None


def remembered_villagers(world: World, agent: Agent) -> list[str]:
    key = villager_key(agent)
    names = []
    for observer in world.living_agents():
        if observer is agent:
            continue
        memory = getattr(observer, "social_memory", {})
        entry = memory.get(key) if memory is not None else None
        if entry is None:
            continue
        if familiarity_level(entry.familiarity_score) == FAMILIAR:
            names.append(observer.name)
    return sorted(names)


def create_remembrance(world: World, agent: Agent, remembered_by: list[str]):
    if not remembered_by:
        return

    remembered_names = set(remembered_by)
    expires_day = world.day + REMEMBRANCE_DURATION_DAYS
    for observer in world.living_agents():
        if observer.name in remembered_names:
            observer.remembering = agent.name
            observer.remembrance_expires_day = expires_day


def expire_remembrances(world: World):
    for agent in world.living_agents():
        if active_remembrance_name(agent, world) is None:
            agent.remembering = None
            agent.remembrance_expires_day = 0


def active_remembrance_name(agent: Agent, world: World | None = None) -> str | None:
    name = getattr(agent, "remembering", None)
    if not name:
        return None
    expires_day = getattr(agent, "remembrance_expires_day", 0)
    if world is not None and expires_day and world.day >= expires_day:
        return None
    return name


def record_death_history(world: World, record: DeathRecord):
    description = death_history_description(record)
    world.history.record(
        day=record.day,
        year=record.year,
        season=record.season,
        category=DEATH,
        title=f"{record.name} Dies",
        description=description,
    )
    world.log(description)


def death_history_description(record: DeathRecord) -> str:
    phrase = villager_phrase(record)
    description = f"{record.name}, {phrase}, died of {record.cause_of_death}."
    if record.remembered_by:
        description += f" They were remembered by {format_names(record.remembered_by)}."
    return description


def villager_phrase(record: DeathRecord) -> str:
    parts = []
    if record.peak_influence_label == "Respected":
        parts.append("respected")
    elif record.peak_influence_label == "Notable":
        parts.append("notable")
    if record.lifecycle_stage:
        parts.append(record.lifecycle_stage)
    if record.role:
        parts.append(record.role)
    words = " ".join(parts) if parts else "villager"
    article = "an" if words[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
    return f"{article} {words}"


def format_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"
