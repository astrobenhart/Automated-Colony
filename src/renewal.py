from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.config import (
    NATURAL_DEATH_CHRONICLE_MIN_AGE,
    NATURAL_DEATH_DAILY_CHANCE_CAP,
    NATURAL_DEATH_EXPECTED_LIFESPAN_MAX,
    NATURAL_DEATH_EXPECTED_LIFESPAN_MIN,
    NATURAL_DEATH_MIN_AGE,
)
from src.death_memory import record_death
from src.generations import FAMILY
from src.lifecycle import ELDER, OLDER_ADULT
from src.social_memory import villager_key

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


@dataclass(frozen=True)
class NaturalDeathCandidate:
    villager_id: str
    name: str
    age: int
    expected_lifespan: int
    daily_chance: float


def update_renewal(world: World) -> list[NaturalDeathCandidate]:
    """Daily renewal pass for old-age mortality and succession-friendly turnover."""
    deaths: list[NaturalDeathCandidate] = []
    rng = random.Random(f"{getattr(world, 'seed', None)}|renewal|{world.day}|{world.year}")
    for agent in list(world.living_agents()):
        ensure_expected_lifespan(world, agent)
        chance = natural_death_daily_chance(agent)
        if chance <= 0:
            continue
        if rng.random() <= chance:
            agent.alive = False
            candidate = NaturalDeathCandidate(
                villager_id=villager_key(agent),
                name=agent.name,
                age=getattr(agent, "age", 0),
                expected_lifespan=getattr(agent, "expected_lifespan", 0) or 0,
                daily_chance=chance,
            )
            deaths.append(candidate)
            record_death(world, agent, "old age")
            record_natural_death_milestone(world, agent)

    if deaths:
        world.natural_deaths_by_year = getattr(world, "natural_deaths_by_year", {})
        world.natural_deaths_by_year[world.year] = world.natural_deaths_by_year.get(world.year, 0) + len(deaths)
        world.update_settlement_population()
    return deaths


def ensure_expected_lifespan(world: World, agent: Agent) -> int:
    lifespan = getattr(agent, "expected_lifespan", None)
    if lifespan is not None:
        return lifespan
    rng = random.Random(f"{getattr(world, 'seed', None)}|lifespan|{villager_key(agent)}")
    baseline = rng.randint(NATURAL_DEATH_EXPECTED_LIFESPAN_MIN, NATURAL_DEATH_EXPECTED_LIFESPAN_MAX)
    trait = str(getattr(agent, "trait", "") or "").lower()
    if trait in {"resilient", "stubborn", "calm"}:
        baseline += 2
    if trait in {"frail", "reckless"}:
        baseline -= 2
    agent.expected_lifespan = max(NATURAL_DEATH_MIN_AGE, baseline)
    return agent.expected_lifespan


def natural_death_daily_chance(agent: Agent) -> float:
    age = int(getattr(agent, "age", 0))
    lifespan = getattr(agent, "expected_lifespan", None)
    if lifespan is None or age < NATURAL_DEATH_MIN_AGE:
        return 0.0

    years_past_minimum = max(0, age - NATURAL_DEATH_MIN_AGE)
    years_past_lifespan = max(0, age - lifespan)
    chance = 0.00010 + years_past_minimum * 0.000035 + years_past_lifespan * 0.00045
    if getattr(agent, "lifecycle_stage", None) == OLDER_ADULT:
        chance *= 0.35
    if getattr(agent, "lifecycle_stage", None) == ELDER:
        chance *= 1.15
    chance *= wellbeing_modifier(agent)
    return min(NATURAL_DEATH_DAILY_CHANCE_CAP, max(0.0, chance))


def wellbeing_modifier(agent: Agent) -> float:
    pressure = 0
    pressure += 1 if getattr(agent, "hunger", 0) >= 70 else 0
    pressure += 1 if getattr(agent, "thirst", 0) >= 70 else 0
    pressure += 1 if getattr(agent, "fatigue", 0) >= 80 else 0
    if pressure == 0:
        return 0.90
    return 1.0 + pressure * 0.18


def record_natural_death_milestone(world: World, agent: Agent) -> None:
    age = getattr(agent, "age", 0)
    if age < NATURAL_DEATH_CHRONICLE_MIN_AGE:
        return
    family = getattr(world, "families", {}).get(getattr(agent, "family_id", None))
    family_text = f" of {family.family_name}" if family is not None else ""
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=FAMILY,
        title="Generation Passes",
        description=f"{agent.name}{family_text} passed peacefully at age {age}.",
    )


def expected_deaths_this_year(world: World) -> float:
    return sum(natural_death_daily_chance(agent) for agent in world.living_agents()) * 80


def age_distribution(world: World) -> Counter:
    buckets: Counter[str] = Counter()
    for agent in world.living_agents():
        age = getattr(agent, "age", 0)
        if age < 18:
            buckets["0-17"] += 1
        elif age < 30:
            buckets["18-29"] += 1
        elif age < 50:
            buckets["30-49"] += 1
        elif age < 65:
            buckets["50-64"] += 1
        else:
            buckets["65+"] += 1
    return buckets


def generation_distribution(world: World) -> Counter:
    return Counter(getattr(agent, "generation", 0) for agent in world.living_agents())
