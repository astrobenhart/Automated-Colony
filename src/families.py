from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from src.generations import FAMILY, MEMORY_CHILD, MEMORY_FAMILY_LOSS, FamilyMemoryRecord, InheritanceProfile
from src.social_memory import villager_key
from src.traits import TRAITS

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


@dataclass
class Family:
    family_id: str
    family_name: str
    founder_ids: list[str] = field(default_factory=list)
    founding_year: int = 1
    generation_count: int = 1
    living_member_ids: list[str] = field(default_factory=list)
    deceased_member_ids: list[str] = field(default_factory=list)
    member_ids: list[str] = field(default_factory=list)
    parent_family_ids: list[str] = field(default_factory=list)
    family_history: list[FamilyMemoryRecord] = field(default_factory=list)
    births_by_year: dict[int, int] = field(default_factory=dict)

    def add_member(self, member_id: str, *, alive: bool = True, generation: int = 0) -> None:
        if member_id not in self.member_ids:
            self.member_ids.append(member_id)
        target = self.living_member_ids if alive else self.deceased_member_ids
        other = self.deceased_member_ids if alive else self.living_member_ids
        if member_id not in target:
            target.append(member_id)
        if member_id in other:
            other.remove(member_id)
        self.generation_count = max(self.generation_count, generation + 1)

    def record_memory(self, memory: FamilyMemoryRecord) -> None:
        if not any(existing.description == memory.description and existing.day == memory.day for existing in self.family_history):
            self.family_history.insert(0, memory)
            self.family_history = self.family_history[:24]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["family_history"] = [memory.to_dict() for memory in self.family_history]
        return data


def ensure_family_registry(world: World) -> dict[str, Family]:
    families = getattr(world, "families", None)
    if families is None:
        world.families = {}
    ensure_all_villagers_have_families(world)
    return world.families


def ensure_all_villagers_have_families(world: World) -> None:
    if getattr(world, "families", None) is None:
        world.families = {}
    for agent in world.agents:
        if getattr(agent, "family_id", None):
            register_family_member(world, agent)
            continue
        family = starting_family_for_agent(world, agent)
        agent.family_id = family.family_id
        register_family_member(world, agent)


def starting_family_for_agent(world: World, agent: Agent) -> Family:
    household_id = getattr(agent, "household_id", None)
    if household_id:
        family_id = f"family-{household_id}"
    else:
        family_id = f"family-{villager_key(agent)}"
    family = world.families.get(family_id)
    if family is None:
        founder_id = villager_key(agent)
        family = Family(
            family_id=family_id,
            family_name=family_name_for_agent(agent),
            founder_ids=[founder_id],
            founding_year=family_founding_year(world, agent),
        )
        family.record_memory(FamilyMemoryRecord(
            category=FAMILY,
            subject_id=founder_id,
            description=f"{family.family_name} is remembered from the early years of the village.",
            year=family.founding_year,
            day=1,
        ))
        world.families[family_id] = family
    return family


def family_name_for_agent(agent: Agent) -> str:
    return f"{getattr(agent, 'name', 'Unknown')} Lineage"


def family_founding_year(world: World, agent: Agent) -> int:
    birth_year = getattr(agent, "birth_year", None)
    if birth_year is not None:
        return max(1, birth_year)
    age = max(0, int(getattr(agent, "age", 0)))
    return max(1, getattr(world, "year", 1) - age)


def register_family_member(world: World, agent: Agent) -> Family:
    family_id = getattr(agent, "family_id", None)
    if not family_id:
        family = starting_family_for_agent(world, agent)
        agent.family_id = family.family_id
    else:
        family = world.families.get(family_id)
        if family is None:
            family = Family(
                family_id=family_id,
                family_name=f"{getattr(agent, 'name', 'Unknown')} Lineage",
                founder_ids=[villager_key(agent)],
                founding_year=family_founding_year(world, agent),
            )
            world.families[family_id] = family
    family.add_member(
        villager_key(agent),
        alive=getattr(agent, "alive", False),
        generation=getattr(agent, "generation", 0),
    )
    return family


def assign_child_family(world: World, child: Agent, parent_a: Agent, parent_b: Agent) -> Family:
    ensure_family_registry(world)
    parent_family_id = getattr(parent_a, "family_id", None) or getattr(parent_b, "family_id", None)
    if parent_family_id is None:
        parent_family_id = register_family_member(world, parent_a).family_id
    child.family_id = parent_family_id
    family = register_family_member(world, child)
    other_family_id = getattr(parent_b, "family_id", None)
    if other_family_id and other_family_id != family.family_id and other_family_id not in family.parent_family_ids:
        family.parent_family_ids.append(other_family_id)
    family.births_by_year[world.year] = family.births_by_year.get(world.year, 0) + 1
    return family


def link_family_relationships(world: World, child: Agent, parent_a: Agent, parent_b: Agent) -> None:
    parent_ids = {villager_key(parent_a), villager_key(parent_b)}
    sibling_ids = set()
    for sibling in world.agents:
        if sibling is child:
            continue
        if set(getattr(sibling, "parent_ids", [])) & parent_ids:
            sibling_ids.add(villager_key(sibling))
            sibling.sibling_ids = sorted(set(getattr(sibling, "sibling_ids", [])) | {villager_key(child)})
            sibling.sync_generation_architecture()
    child.sibling_ids = sorted(set(getattr(child, "sibling_ids", [])) | sibling_ids)
    child.sync_generation_architecture()


def inherited_profile(parent_a: Agent, parent_b: Agent, child_trait: str, rng: random.Random) -> InheritanceProfile:
    profile = InheritanceProfile()
    profile.personality_traits = unique_limited(
        [child_trait, getattr(parent_a, "trait", None), getattr(parent_b, "trait", None)],
        limit=3,
    )
    if rng.random() < 0.16:
        variation = rng.choice(TRAITS)
        if variation not in profile.personality_traits:
            profile.personality_traits.append(variation)
    profile.work_preferences = unique_limited(
        [getattr(parent_a, "role", None), getattr(parent_b, "role", None)],
        limit=3,
    )
    profile.social_tendencies = unique_limited(
        [getattr(parent_a, "experience_level", None), getattr(parent_b, "experience_level", None)],
        limit=2,
    )
    profile.appearance_traits = {
        "parent_a_appearance": getattr(parent_a, "appearance_type", None),
        "parent_b_appearance": getattr(parent_b, "appearance_type", None),
    }
    return profile


def unique_limited(values: list[object], limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        if not value:
            continue
        text = str(value)
        if text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def record_family_birth(world: World, family: Family, parent_a: Agent, parent_b: Agent, child: Agent) -> None:
    child_id = villager_key(child)
    birth_count = sum(family.births_by_year.values())
    if birth_count == 1:
        description = f"{family.family_name} welcomed {child.name}, its first child recorded in the village Chronicle."
        title = "Family Child"
    else:
        description = f"{family.family_name} welcomed {child.name} into generation {getattr(child, 'generation', 0) + 1}."
        title = "Family Birth"
    memory = FamilyMemoryRecord(
        category=MEMORY_CHILD,
        subject_id=child_id,
        description=description,
        year=world.year,
        day=world.day,
    )
    family.record_memory(memory)
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=FAMILY,
        title=title,
        description=description,
    )
    if family.generation_count >= 3:
        milestone = f"{family.family_name} now spans {family.generation_count} generations."
        family.record_memory(FamilyMemoryRecord(
            category=FAMILY,
            subject_id=child_id,
            description=milestone,
            year=world.year,
            day=world.day,
        ))
        world.history.record(
            day=world.day,
            year=world.year,
            season=world.season,
            category=FAMILY,
            title="Family Generations",
            description=milestone,
        )


def record_family_adulthood(world: World, agent: Agent) -> None:
    family = family_for_agent(world, agent)
    if family is None:
        return
    description = f"{agent.name} of {family.family_name} reached adulthood."
    family.record_memory(FamilyMemoryRecord(
        category=FAMILY,
        subject_id=villager_key(agent),
        description=description,
        year=world.year,
        day=world.day,
    ))


def record_family_death(world: World, agent: Agent) -> None:
    ensure_family_registry(world)
    family = family_for_agent(world, agent)
    if family is None:
        return
    register_family_member(world, agent)
    subject_id = villager_key(agent)
    if subject_id in family.living_member_ids:
        family.living_member_ids.remove(subject_id)
    if subject_id not in family.deceased_member_ids:
        family.deceased_member_ids.append(subject_id)
    is_founder = subject_id in family.founder_ids
    description = (
        f"{family.family_name} lost its founder, {agent.name}."
        if is_founder
        else f"{family.family_name} remembered the passing of {agent.name}."
    )
    family.record_memory(FamilyMemoryRecord(
        category=MEMORY_FAMILY_LOSS,
        subject_id=subject_id,
        description=description,
        year=world.year,
        day=world.day,
    ))
    if is_founder and len(family.member_ids) > 1:
        world.history.record(
            day=world.day,
            year=world.year,
            season=world.season,
            category=FAMILY,
            title="Founder Lost",
            description=description,
        )


def family_for_agent(world: World, agent: Agent) -> Family | None:
    family_id = getattr(agent, "family_id", None)
    if not family_id:
        return None
    return getattr(world, "families", {}).get(family_id)


def family_rows(world: World) -> list[tuple[str, object]]:
    families = list((getattr(world, "families", {}) or {}).values())
    living_sizes = [len(family.living_member_ids) for family in families]
    largest = max(families, key=lambda family: len(family.living_member_ids), default=None)
    oldest = min(families, key=lambda family: family.founding_year, default=None)
    generations = max((family.generation_count for family in families), default=0)
    births_this_year = sum(family.births_by_year.get(world.year, 0) for family in families)
    return [
        ("Families", len(families)),
        ("Average Family Size", f"{(sum(living_sizes) / len(living_sizes)):.1f}" if living_sizes else "0.0"),
        ("Largest Family", largest.family_name if largest is not None else "None"),
        ("Largest Family Size", max(living_sizes) if living_sizes else 0),
        ("Oldest Family", oldest.family_name if oldest is not None else "None"),
        ("Current Generations", generations),
        ("Births By Family This Year", births_this_year),
    ]
