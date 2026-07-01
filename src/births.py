from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.appearance import appearance_seed_for, appearance_type_for_seed
from src.config import (
    BIRTH_DAILY_CHANCE,
    BIRTH_DAILY_CHANCE_CAP,
    BIRTH_FOOD_RESERVE_DAYS,
    BIRTH_MAX_DEPENDENT_CHILDREN_PER_HOUSEHOLD,
    BIRTH_MAX_PER_DAY,
    BIRTH_MIN_CHILD_SPACING_YEARS,
    BIRTH_MIN_PARTNERSHIP_YEARS,
    BIRTH_RENEWAL_MULTIPLIER_CRITICAL_PRESSURE,
    BIRTH_RENEWAL_MULTIPLIER_LOW_PRESSURE,
    BIRTH_RENEWAL_MULTIPLIER_VERY_LOW_PRESSURE,
    BIRTH_RENEWAL_PRESSURE_LOW,
    BIRTH_RENEWAL_PRESSURE_STABLE,
    BIRTH_RENEWAL_PRESSURE_VERY_LOW,
    BIRTH_SCORE_CHANCE_FACTOR,
    BIRTH_WATER_RESERVE_DAYS,
    HOME_WANDER_MAX_RADIUS,
    HOME_WANDER_MIN_RADIUS,
    SETTLEMENT_FOOD_TARGET_DAYS,
    SETTLEMENT_WATER_TARGET_DAYS,
)
from src.families import (
    assign_child_family,
    inherited_profile,
    link_family_relationships,
    record_family_birth,
)
from src.generations import BIRTH, MEMORY_CHILD, FamilyMemoryRecord
from src.lifecycle import ADULT, CHILD, OLDER_ADULT, YOUNG_ADULT
from src.roles import GENERALIST
from src.social_memory import villager_key
from src.traits import TRAITS

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


BIRTH_PARENT_STAGES = {YOUNG_ADULT, ADULT, OLDER_ADULT}
CHILD_NAMES = (
    "Mara", "Elric", "Rowan", "Tessa", "Nia",
    "Oren", "Lio", "Sera", "Kael", "Mina",
)


@dataclass(frozen=True)
class BirthCandidate:
    parent_a: Agent
    parent_b: Agent
    score: int


def update_births(world: World) -> list[Agent]:
    """Run the daily household renewal pass."""
    rng = random.Random(f"{getattr(world, 'seed', None)}|births|{world.day}")
    candidates = birth_candidates(world)
    if not candidates:
        return []

    rng.shuffle(candidates)
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)

    births: list[Agent] = []
    used_parents: set[str] = set()
    renewal_multiplier = population_renewal_multiplier(world)
    for candidate in candidates:
        if len(births) >= BIRTH_MAX_PER_DAY:
            break
        parent_ids = {villager_key(candidate.parent_a), villager_key(candidate.parent_b)}
        if used_parents & parent_ids:
            continue
        chance = birth_chance(candidate.score, renewal_multiplier=renewal_multiplier)
        record_birth_attempt(world)
        if rng.random() > chance:
            continue
        births.append(create_child(world, candidate.parent_a, candidate.parent_b, rng=rng))
        used_parents.update(parent_ids)

    return births


def record_birth_attempt(world: World):
    world.birth_attempts_total = getattr(world, "birth_attempts_total", 0) + 1
    attempts_by_year = getattr(world, "birth_attempts_by_year", None)
    if attempts_by_year is not None:
        attempts_by_year[world.year] = attempts_by_year.get(world.year, 0) + 1


def record_birth_success(world: World):
    world.successful_births_total = getattr(world, "successful_births_total", 0) + 1
    successes_by_year = getattr(world, "successful_births_by_year", None)
    if successes_by_year is not None:
        successes_by_year[world.year] = successes_by_year.get(world.year, 0) + 1


def birth_candidates(world: World) -> list[BirthCandidate]:
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    candidates: list[BirthCandidate] = []
    seen_pairs: set[frozenset[str]] = set()

    for parent_a in living_by_id.values():
        partner_id = getattr(parent_a, "partner_id", None)
        if not partner_id or partner_id not in living_by_id:
            continue
        parent_b = living_by_id[partner_id]
        pair_key = frozenset((villager_key(parent_a), villager_key(parent_b)))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        if not birth_eligible(world, parent_a, parent_b):
            continue
        candidates.append(BirthCandidate(parent_a, parent_b, birth_score(world, parent_a, parent_b)))

    return candidates


def birth_eligible(world: World, parent_a: Agent, parent_b: Agent) -> bool:
    if getattr(world, "settlement", None) is None:
        return False
    if parent_a is parent_b:
        return False
    if not is_birth_parent(parent_a) or not is_birth_parent(parent_b):
        return False
    if getattr(parent_a, "partner_id", None) != villager_key(parent_b):
        return False
    if getattr(parent_b, "partner_id", None) != villager_key(parent_a):
        return False
    if getattr(parent_a, "partnership_duration", 0) < BIRTH_MIN_PARTNERSHIP_YEARS:
        return False
    if getattr(parent_b, "partnership_duration", 0) < BIRTH_MIN_PARTNERSHIP_YEARS:
        return False
    if getattr(parent_a, "household_id", None) != getattr(parent_b, "household_id", None):
        return False
    if not getattr(parent_a, "household_id", None):
        return False
    if settlement_id(parent_a) != settlement_id(parent_b):
        return False
    if settlement_id(parent_a) != world.settlement.settlement_id:
        return False
    if not household_can_support_birth(world, parent_a):
        return False
    if not household_birth_spacing_allows(world, parent_a, parent_b):
        return False
    if not resources_support_birth(world):
        return False
    return True


def birth_chance(score: int, renewal_multiplier: float = 1.0) -> float:
    base_chance = min(BIRTH_DAILY_CHANCE_CAP, BIRTH_DAILY_CHANCE + max(0, score - 60) * BIRTH_SCORE_CHANCE_FACTOR)
    return min(1.0, base_chance * max(1.0, renewal_multiplier))


def population_renewal_multiplier(world: World) -> float:
    """Slightly lift birth chance when homes are underused.

    Eligibility gates stay unchanged; this only affects the final probability
    after a partnered household already qualifies for birth.
    """
    capacity = total_housing_capacity(world)
    if capacity <= 0:
        return 1.0
    pressure = len(world.living_agents()) / max(1, capacity)
    if pressure < BIRTH_RENEWAL_PRESSURE_VERY_LOW:
        return BIRTH_RENEWAL_MULTIPLIER_CRITICAL_PRESSURE
    if pressure < BIRTH_RENEWAL_PRESSURE_LOW:
        return BIRTH_RENEWAL_MULTIPLIER_VERY_LOW_PRESSURE
    if pressure < BIRTH_RENEWAL_PRESSURE_STABLE:
        return BIRTH_RENEWAL_MULTIPLIER_LOW_PRESSURE
    return 1.0


def total_housing_capacity(world: World) -> int:
    from src.residential import all_household_statuses

    return sum(status.capacity for status in all_household_statuses(world))


def is_birth_parent(agent: Agent) -> bool:
    return getattr(agent, "alive", False) and getattr(agent, "lifecycle_stage", None) in BIRTH_PARENT_STAGES


def settlement_id(agent: Agent) -> str | None:
    return getattr(agent, "home_settlement_id", None) or getattr(agent, "birth_settlement_id", None)


def household_can_support_birth(world: World, parent_a: Agent) -> bool:
    from src.config import MAX_HOUSE_TILES_PER_HOUSEHOLD
    from src.residential import household_capacity, household_homes, household_occupants

    household = world.household_for_agent(parent_a)
    if household is None:
        return False
    occupants = len(household_occupants(world, household))
    capacity = household_capacity(world, household)
    house_tiles = len(household_homes(world, household))
    if capacity <= 0:
        return False
    if occupants < capacity:
        return True
    return house_tiles < MAX_HOUSE_TILES_PER_HOUSEHOLD


def resources_support_birth(world: World) -> bool:
    population = max(1, len(world.living_agents()))
    food_target = population * min(BIRTH_FOOD_RESERVE_DAYS, SETTLEMENT_FOOD_TARGET_DAYS)
    water_target = population * min(BIRTH_WATER_RESERVE_DAYS, SETTLEMENT_WATER_TARGET_DAYS)
    return effective_birth_food(world, population) >= food_target and effective_birth_water(world, population) >= water_target


def household_birth_spacing_allows(world: World, parent_a: Agent, parent_b: Agent) -> bool:
    household_id = getattr(parent_a, "household_id", None)
    parent_ids = {villager_key(parent_a), villager_key(parent_b)}
    dependent_children = [
        agent
        for agent in world.living_agents()
        if (
            getattr(agent, "household_id", None) == household_id
            and getattr(agent, "lifecycle_stage", None) == CHILD
        )
    ]
    if len(dependent_children) >= BIRTH_MAX_DEPENDENT_CHILDREN_PER_HOUSEHOLD:
        return False
    shared_children = [
        child
        for child in dependent_children
        if parent_ids & set(getattr(child, "parent_ids", []) or [])
    ]
    if not shared_children:
        return True
    youngest_age = min(getattr(child, "age", 0) for child in shared_children)
    return youngest_age >= BIRTH_MIN_CHILD_SPACING_YEARS


def effective_birth_food(world: World, population: int) -> int:
    settlement = getattr(world, "settlement", None)
    stored_food = world.colony_storage.food
    if settlement is None:
        return stored_food
    from src.settlement import refresh_local_resource_cache

    refresh_local_resource_cache(world)
    ready_farm_food = sum(farm.food for farm in settlement.farm_plots if farm.active)
    local_food = len(getattr(settlement, "local_food", set()))
    return stored_food + ready_farm_food + min(local_food, population)


def effective_birth_water(world: World, population: int) -> int:
    settlement = getattr(world, "settlement", None)
    stored_water = world.colony_storage.water
    if settlement is None:
        return stored_water
    from src.settlement import refresh_local_resource_cache

    refresh_local_resource_cache(world)
    local_water = len(getattr(settlement, "local_water", set()))
    return stored_water + min(local_water * 3, population)


def birth_score(world: World, parent_a: Agent, parent_b: Agent) -> int:
    duration = min(8, getattr(parent_a, "partnership_duration", 0))
    household = world.household_for_agent(parent_a)
    household_stability = min(10, getattr(household, "established_years", 0)) if household is not None else 0
    food_buffer = min(12, world.colony_storage.food // max(1, len(world.living_agents())))
    water_buffer = min(8, world.colony_storage.water // max(1, len(world.living_agents())))
    return 40 + duration * 4 + household_stability + food_buffer + water_buffer


def create_child(world: World, parent_a: Agent, parent_b: Agent, rng: random.Random | None = None) -> Agent:
    from src.agent import Agent

    rng = rng or random.Random(f"{getattr(world, 'seed', None)}|birth|{world.day}|{len(world.agents)}")
    child_id = next_child_id(world)
    child_name = child_name_for(world, rng)
    household = world.household_for_agent(parent_a)
    home_x = getattr(parent_a, "home_x", None)
    home_y = getattr(parent_a, "home_y", None)
    x = home_x if home_x is not None else parent_a.x
    y = home_y if home_y is not None else parent_a.y
    appearance_seed = appearance_seed_for(getattr(world, "seed", None), len(world.agents), child_name)
    trait = inherited_trait(parent_a, parent_b, rng)

    child = Agent(
        child_name,
        x,
        y,
        role=GENERALIST,
        lifecycle_stage=CHILD,
        age=0,
        experience_level="Novice",
        trait=trait,
        agent_id=child_id,
        appearance_seed=appearance_seed,
        appearance_type=appearance_type_for_seed(appearance_seed),
        home_settlement_id=getattr(parent_a, "home_settlement_id", None),
        home_settlement_name=getattr(parent_a, "home_settlement_name", None),
        household_id=getattr(parent_a, "household_id", None),
        home_id=getattr(parent_a, "home_id", None),
        home_x=home_x,
        home_y=home_y,
        birth_settlement_id=getattr(parent_a, "home_settlement_id", None),
        birth_settlement_name=getattr(parent_a, "home_settlement_name", None),
        birth_year=world.year,
        birth_day=world.day,
        parent_a_id=villager_key(parent_a),
        parent_b_id=villager_key(parent_b),
        parent_ids=[villager_key(parent_a), villager_key(parent_b)],
        generation=max(getattr(parent_a, "generation", 0), getattr(parent_b, "generation", 0)) + 1,
        current_action="At home",
        current_goal="Grow",
        daily_role=None,
        home_wander_radius=rng.randint(HOME_WANDER_MIN_RADIUS, HOME_WANDER_MAX_RADIUS),
    )
    child.inheritance_profile = inherited_profile(parent_a, parent_b, trait, rng)
    from src.renewal import ensure_expected_lifespan

    ensure_expected_lifespan(world, child)

    world.agents.append(child)
    if household is not None:
        world.add_agent_to_household(child, household)
    family = assign_child_family(world, child, parent_a, parent_b)
    link_parent_child(parent_a, child)
    link_parent_child(parent_b, child)
    link_family_relationships(world, child, parent_a, parent_b)
    record_birth_memories(world, parent_a, parent_b, child, household)
    record_birth_history(world, parent_a, parent_b, child, household)
    record_family_birth(world, family, parent_a, parent_b, child)
    record_birth_success(world)
    world.update_settlement_population()
    child.sync_generation_architecture()
    return child


def next_child_id(world: World) -> str:
    existing = {villager_key(agent) for agent in world.agents}
    index = len(world.agents)
    while f"child-{index}" in existing:
        index += 1
    return f"child-{index}"


def child_name_for(world: World, rng: random.Random) -> str:
    existing_names = {agent.name for agent in world.agents}
    for _ in range(len(CHILD_NAMES) * 2):
        name = rng.choice(CHILD_NAMES)
        if name not in existing_names:
            return name
    return f"Child {len(world.agents) + 1}"


def inherited_trait(parent_a: Agent, parent_b: Agent, rng: random.Random) -> str:
    parent_traits = [trait for trait in (getattr(parent_a, "trait", None), getattr(parent_b, "trait", None)) if trait]
    if parent_traits and rng.random() >= 0.12:
        return rng.choice(parent_traits)
    return rng.choice(TRAITS)


def link_parent_child(parent: Agent, child: Agent):
    child_id = villager_key(child)
    if child_id not in parent.child_ids:
        parent.child_ids.append(child_id)
    if child_id not in parent.children_ids:
        parent.children_ids.append(child_id)
    parent.sync_generation_architecture()


def record_birth_memories(world: World, parent_a: Agent, parent_b: Agent, child: Agent, household):
    child_memory = (
        f"Born into {household.household_name} in Year {world.year}."
        if household is not None
        else f"Born in Year {world.year}."
    )
    child.personal_memories.insert(0, child_memory)
    for parent in (parent_a, parent_b):
        memory = f"Welcomed {child.name} into the household in Year {world.year}."
        parent.personal_memories.insert(0, memory)
        parent.family_memories.append(FamilyMemoryRecord(
            category=MEMORY_CHILD,
            subject_id=villager_key(child),
            description=memory,
            year=world.year,
            day=world.day,
        ))


def record_birth_history(world: World, parent_a: Agent, parent_b: Agent, child: Agent, household):
    household_text = f" of {household.household_name}" if household is not None else ""
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=BIRTH,
        title="Birth",
        description=f"{parent_a.name} and {parent_b.name} welcomed {child.name}{household_text}.",
    )
