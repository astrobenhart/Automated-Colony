from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.affection import (
    affection_label,
    affection_mood_bonus,
    average_partnered_gathering_participation,
    has_nearby_partner,
    partners_spending_free_time_together,
)
from src.births import (
    birth_candidates,
    household_can_support_birth,
    household_birth_spacing_allows,
    is_birth_parent,
    resources_support_birth,
    settlement_id,
)
from src.config import SETTLEMENT_FOOD_TARGET_DAYS, SETTLEMENT_WATER_TARGET_DAYS
from src.celebrations import celebration_diagnostics
from src.community import community_diagnostics
from src.families import family_rows
from src.friendships import friendship_diagnostics, has_nearby_close_friend
from src.gatherings import gathering_diagnostics
from src.generations import BIRTH
from src.lifecycle import CHILD
from src.lifecycle_progression import days_until_adulthood
from src.partnerships import partnership_candidates
from src.renewal import age_distribution, expected_deaths_this_year, generation_distribution
from src.residential import all_household_statuses, residential_demand
from src.roles import BUILDER, FORAGER, GENERALIST
from src.settlement_planner import WORK_CONSTRUCTION, WORK_FARMING, WORK_FOOD, WORK_SUPPORT, WORK_WATER, WORK_WOOD
from src.shared_moments import current_shared_moment, shared_moment_diagnostics
from src.social_memory import villager_key


@dataclass(frozen=True)
class DiagnosticSection:
    title: str
    rows: list[tuple[str, object]]


def diagnostics_sections(world, renderer_metrics: dict[str, object] | None = None) -> list[DiagnosticSection]:
    return [
        DiagnosticSection("Population", population_rows(world)),
        DiagnosticSection("Children", children_rows(world)),
        DiagnosticSection("Adults", adults_rows(world)),
        DiagnosticSection("Lifecycle", lifecycle_rows(world)),
        DiagnosticSection("Families", family_rows(world)),
        DiagnosticSection("Households", household_rows(world)),
        DiagnosticSection("Housing", housing_rows(world)),
        DiagnosticSection("Partnerships", partnership_rows(world)),
        DiagnosticSection("Friendships", friendship_rows(world)),
        DiagnosticSection("Gatherings", gathering_rows(world)),
        DiagnosticSection("Shared Moments", shared_moment_rows(world)),
        DiagnosticSection("Celebrations", celebration_rows(world)),
        DiagnosticSection("Living Community", community_rows(world)),
        DiagnosticSection("Births", birth_rows(world)),
        DiagnosticSection("Resources", resource_rows(world)),
        DiagnosticSection("Workforce", workforce_rows(world)),
        DiagnosticSection("Mood", mood_rows(world)),
        DiagnosticSection("Performance", performance_rows(world, renderer_metrics or {})),
    ]


def population_rows(world) -> list[tuple[str, object]]:
    living = world.living_agents()
    children = [agent for agent in living if getattr(agent, "lifecycle_stage", None) == CHILD]
    adults = [agent for agent in living if getattr(agent, "lifecycle_stage", None) != CHILD]
    ages = [getattr(agent, "age", 0) for agent in living]
    oldest = max(living, key=lambda agent: (getattr(agent, "age", 0), agent.name), default=None)
    generations = {getattr(agent, "generation", 0) for agent in living}
    births = len([entry for entry in getattr(world.history, "entries", []) if entry.category == BIRTH])

    return [
        ("Total Population", len(living)),
        ("Adults", len(adults)),
        ("Children", len(children)),
        ("Births", births),
        ("Deaths", len(getattr(world, "death_records", []))),
        ("Average Age", f"{(sum(ages) / len(ages)):.1f}" if ages else "0.0"),
        ("Oldest Villager", oldest.name if oldest is not None else "None"),
        ("Generation Count", len(generations)),
    ]


def children_rows(world) -> list[tuple[str, object]]:
    children = [agent for agent in world.living_agents() if getattr(agent, "lifecycle_stage", None) == CHILD]
    ages = [getattr(agent, "age", 0) for agent in children]
    upcoming_days = [
        days
        for days in (days_until_adulthood(world, agent) for agent in children)
        if days is not None
    ]
    upcoming_transitions = sum(1 for days in upcoming_days if days <= 30)

    return [
        ("Total Children", len(children)),
        ("Average Child Age", f"{(sum(ages) / len(ages)):.1f}" if ages else "0.0"),
        ("Youngest Child", min(ages) if ages else "None"),
        ("Oldest Child", max(ages) if ages else "None"),
        ("Upcoming Adult Transitions", upcoming_transitions),
    ]


def adults_rows(world) -> list[tuple[str, object]]:
    living = world.living_agents()
    adults = [agent for agent in living if getattr(agent, "lifecycle_stage", None) != CHILD]
    workforce_eligible = [agent for agent in adults if getattr(agent, "alive", False) and getattr(agent, "role", None)]

    return [
        ("Total Adults", len(adults)),
        ("Workforce Eligible", len(workforce_eligible)),
        ("Recently Joined Workforce", getattr(world, "adults_this_year", {}).get(world.year, 0)),
    ]


def lifecycle_rows(world) -> list[tuple[str, object]]:
    age_buckets = age_distribution(world)
    generations = generation_distribution(world)
    return [
        ("Adults This Year", getattr(world, "adults_this_year", {}).get(world.year, 0)),
        ("Births This Year", getattr(world, "successful_births_by_year", {}).get(world.year, 0)),
        ("Deaths This Year", deaths_this_year(world)),
        ("Natural Deaths This Year", getattr(world, "natural_deaths_by_year", {}).get(world.year, 0)),
        ("Expected Deaths This Year", f"{expected_deaths_this_year(world):.2f}"),
        ("Age Distribution", format_counter(age_buckets)),
        ("Generation Distribution", format_generation_counter(generations)),
    ]


def deaths_this_year(world) -> int:
    return sum(1 for record in getattr(world, "death_records", []) if getattr(record, "year", None) == world.year)


def household_rows(world) -> list[tuple[str, object]]:
    settlement = getattr(world, "settlement", None)
    statuses = all_household_statuses(world)
    if settlement is None:
        return [("Total Households", 0)]
    demand = residential_demand(world)
    requesting_expansion = sum(1 for status in statuses if status.overcrowded_by > 0 and status.expansion_site is not None)
    requesting_new = sum(1 for status in statuses if status.homeless)
    if demand is not None and demand.demand_type == "split_household":
        requesting_new += 1

    return [
        ("Total Households", settlement.household_count),
        ("Total Homes", len(settlement.homes)),
        ("Average Household Size", f"{settlement.average_household_size:.1f}"),
        ("Largest Household", settlement.largest_household_size),
        ("Overcrowded Households", sum(1 for status in statuses if status.overcrowded_by > 0)),
        ("Households Without Homes", sum(1 for status in statuses if status.homeless)),
        ("Households Requesting Expansion", requesting_expansion),
        ("Households Requesting New Housing", requesting_new),
        ("Succession Events This Year", getattr(world, "household_succession_events_by_year", {}).get(world.year, 0)),
        ("Split Events This Year", getattr(world, "household_split_events_by_year", {}).get(world.year, 0)),
    ]


def housing_rows(world) -> list[tuple[str, object]]:
    settlement = getattr(world, "settlement", None)
    statuses = all_household_statuses(world)
    homes = list(getattr(settlement, "homes", [])) if settlement is not None else []
    assigned_home_ids = {home.home_id for home in homes if getattr(home, "household_id", None) or (settlement and settlement.household_for_home(home.home_id))}
    occupied_home_ids = set()
    for status in statuses:
        if status.occupants > 0:
            household = settlement.household_for(status.household_id) if settlement is not None else None
            for home in homes:
                if household is not None and (home.household_id == household.household_id or home.home_id in (household.home_id, household.home_building_id)):
                    occupied_home_ids.add(home.home_id)
    size_counts = Counter(status.house_tiles for status in statuses)
    pending_expansions = sum(1 for status in statuses if status.overcrowded_by > 0 and status.expansion_site is not None)
    shortages = sum(1 for status in statuses if status.overcrowded_by > 0 or status.homeless)

    return [
        ("Total Capacity", sum(status.capacity for status in statuses)),
        ("Current Occupants", len(world.living_agents())),
        ("Occupied Homes", len(occupied_home_ids)),
        ("Vacant Homes", max(0, len(homes) - len(assigned_home_ids))),
        ("1-Tile Homes", size_counts.get(1, 0)),
        ("2-Tile Homes", size_counts.get(2, 0)),
        ("3-Tile Homes", size_counts.get(3, 0)),
        ("Pending Expansions", pending_expansions),
        ("Housing Shortages", shortages),
    ]


def partnership_rows(world) -> list[tuple[str, object]]:
    living = world.living_agents()
    adult_stages = {"Young Adult", "Adult", "Older Adult", "Elder"}
    adults = [agent for agent in living if getattr(agent, "lifecycle_stage", None) in adult_stages]
    partnered_ids = set()
    pairs = []
    for agent in adults:
        agent_id = villager_key(agent)
        partner_id = getattr(agent, "partner_id", None)
        if partner_id and agent_id not in partnered_ids:
            pairs.append(agent)
            partnered_ids.add(agent_id)
            partnered_ids.add(partner_id)
    durations = [getattr(agent, "partnership_duration", 0) for agent in pairs]
    affection_labels = Counter(affection_label(agent) for agent in pairs)
    partnered_adults = [agent for agent in adults if getattr(agent, "partner_id", None)]

    return [
        ("Active Partnerships", len(pairs)),
        ("Eligible Partnerships", len(partnership_candidates(world))),
        ("Average Partnership Duration", f"{(sum(durations) / len(durations)):.1f} years" if durations else "0.0 years"),
        ("Strong Partnerships", affection_labels["Strong"] + affection_labels["Lifelong"]),
        ("Partners Spending Free Time Together", partners_spending_free_time_together(world)),
        ("Partnered Gathering Participation", average_partnered_gathering_participation(world)),
        ("Single Adults", len(adults) - len(partnered_adults)),
        ("Partnered Adults", len(partnered_adults)),
    ]


def birth_rows(world) -> list[tuple[str, object]]:
    blockers = birth_blockers(world)
    return [
        ("Births This Year", getattr(world, "successful_births_by_year", {}).get(world.year, 0)),
        ("Eligible Pairs", len(birth_candidates(world))),
        ("Birth Attempts", getattr(world, "birth_attempts_by_year", {}).get(world.year, 0)),
        ("Successful Births", getattr(world, "successful_births_by_year", {}).get(world.year, 0)),
        ("Blocked By Housing", blockers["housing"]),
        ("Blocked By Resources", blockers["resources"]),
        ("Blocked By Household Rules", blockers["household"]),
        ("Blocked By Other", blockers["other"]),
    ]


def friendship_rows(world) -> list[tuple[str, object]]:
    return friendship_diagnostics(world)


def gathering_rows(world) -> list[tuple[str, object]]:
    return gathering_diagnostics(world)


def shared_moment_rows(world) -> list[tuple[str, object]]:
    return shared_moment_diagnostics(world)


def celebration_rows(world) -> list[tuple[str, object]]:
    return celebration_diagnostics(world)


def community_rows(world) -> list[tuple[str, object]]:
    return community_diagnostics(world)


def birth_blockers(world) -> Counter:
    blockers: Counter[str] = Counter()
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    seen: set[frozenset[str]] = set()
    for parent_a in living_by_id.values():
        partner_id = getattr(parent_a, "partner_id", None)
        if not partner_id or partner_id not in living_by_id:
            continue
        parent_b = living_by_id[partner_id]
        pair_key = frozenset((villager_key(parent_a), villager_key(parent_b)))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        category = birth_blocker_for_pair(world, parent_a, parent_b)
        if category:
            blockers[category] += 1
    return blockers


def birth_blocker_for_pair(world, parent_a, parent_b) -> str | None:
    if not is_birth_parent(parent_a) or not is_birth_parent(parent_b):
        return "other"
    if getattr(parent_a, "partner_id", None) != villager_key(parent_b) or getattr(parent_b, "partner_id", None) != villager_key(parent_a):
        return "other"
    if getattr(parent_a, "household_id", None) != getattr(parent_b, "household_id", None) or not getattr(parent_a, "household_id", None):
        return "household"
    if settlement_id(parent_a) != settlement_id(parent_b) or settlement_id(parent_a) != getattr(getattr(world, "settlement", None), "settlement_id", None):
        return "household"
    from src.config import BIRTH_MIN_PARTNERSHIP_YEARS

    if getattr(parent_a, "partnership_duration", 0) < BIRTH_MIN_PARTNERSHIP_YEARS or getattr(parent_b, "partnership_duration", 0) < BIRTH_MIN_PARTNERSHIP_YEARS:
        return "other"
    if not household_can_support_birth(world, parent_a):
        return "housing"
    if not household_birth_spacing_allows(world, parent_a, parent_b):
        return "household"
    if not resources_support_birth(world):
        return "resources"
    return None


def resource_rows(world) -> list[tuple[str, object]]:
    population = len(world.living_agents())
    food_target = population * SETTLEMENT_FOOD_TARGET_DAYS
    water_target = population * SETTLEMENT_WATER_TARGET_DAYS
    assignments = Counter(getattr(agent, "daily_role", None) for agent in world.living_agents())
    food_workers = assignments[WORK_FOOD] + assignments[WORK_FARMING]
    water_workers = assignments[WORK_WATER]
    wood_workers = assignments[WORK_WOOD]
    estimated_food_consumption = population
    estimated_water_consumption = population
    estimated_wood_consumption = 1 if world.building_priority() is not None else 0

    return [
        ("Food", f"{world.colony_storage.food} / {food_target}"),
        ("Water", f"{world.colony_storage.water} / {water_target}"),
        ("Wood", world.colony_storage.wood),
        ("Daily Production", f"F:{food_workers} W:{water_workers} Wood:{wood_workers} workers"),
        ("Daily Consumption", f"F:{estimated_food_consumption} W:{estimated_water_consumption} Wood:{estimated_wood_consumption} est."),
        ("Food Surplus/Deficit", world.colony_storage.food - food_target),
        ("Water Surplus/Deficit", world.colony_storage.water - water_target),
        ("Wood Surplus/Deficit", world.colony_storage.wood),
    ]


def workforce_rows(world) -> list[tuple[str, object]]:
    assignments = Counter(getattr(agent, "daily_role", None) for agent in world.living_agents())
    roles = Counter(getattr(agent, "role", None) for agent in world.living_agents())
    idle = sum(1 for agent in world.living_agents() if getattr(agent, "task_state", None) == "idle" and getattr(agent, "daily_role", None) in (None, WORK_SUPPORT))
    return [
        ("Farmers", assignments[WORK_FARMING]),
        ("Water Collectors", assignments[WORK_WATER]),
        ("Builders", assignments[WORK_CONSTRUCTION] + roles[BUILDER]),
        ("Woodcutters", assignments[WORK_WOOD]),
        ("Generalists", roles[GENERALIST]),
        ("Idle Villagers", idle),
        ("Foragers", roles[FORAGER]),
    ]


def mood_rows(world) -> list[tuple[str, object]]:
    scores = [derived_mood_score(agent, world) for agent in world.living_agents()]
    happy = sum(1 for score in scores if score >= 70)
    unhappy = sum(1 for score in scores if score < 40)
    neutral = max(0, len(scores) - happy - unhappy)
    positives = Counter()
    negatives = Counter()
    for agent in world.living_agents():
        pos, neg = mood_modifiers(agent, world)
        positives[pos] += 1
        negatives[neg] += 1

    return [
        ("Average Mood", f"{(sum(scores) / len(scores)):.1f}" if scores else "0.0"),
        ("Happy", happy),
        ("Neutral", neutral),
        ("Unhappy", unhappy),
        ("Top Positive Modifier", positives.most_common(1)[0][0] if positives else "None"),
        ("Top Negative Modifier", negatives.most_common(1)[0][0] if negatives else "None"),
    ]


def derived_mood_score(agent, world) -> int:
    score = 80
    score -= min(30, getattr(agent, "hunger", 0) // 3)
    score -= min(30, getattr(agent, "thirst", 0) // 3)
    score -= min(20, getattr(agent, "fatigue", 0) // 5)
    household = world.household_for_agent(agent) if hasattr(world, "household_for_agent") else None
    if household is not None:
        statuses = {status.household_id: status for status in all_household_statuses(world)}
        status = statuses.get(household.household_id)
        if status is not None and status.overcrowded_by > 0:
            score -= min(20, status.overcrowded_by * 5)
    if has_nearby_close_friend(agent, world):
        score += 3
    score += affection_mood_bonus(agent, world)
    if current_shared_moment(agent, world):
        score += 2
    if getattr(agent, "remembering", None):
        score -= 4
    return max(0, min(100, score))


def mood_modifiers(agent, world) -> tuple[str, str]:
    positive = "Household stability" if getattr(agent, "household_id", None) else "Basic needs met"
    if getattr(agent, "partner_id", None):
        positive = "Partnered"
    if has_nearby_partner(agent, world) and affection_label(agent) in {"Established", "Strong", "Lifelong"}:
        positive = "Near partner"
    if has_nearby_close_friend(agent, world):
        positive = "Near close friend"
    if current_shared_moment(agent, world):
        positive = "Shared moment"
    negative = "None"
    if getattr(agent, "thirst", 0) >= 70:
        negative = "Thirst"
    elif getattr(agent, "hunger", 0) >= 70:
        negative = "Hunger"
    elif getattr(agent, "fatigue", 0) >= 70:
        negative = "Fatigue"
    elif getattr(agent, "remembering", None):
        negative = "Mourning"
    else:
        household = world.household_for_agent(agent) if hasattr(world, "household_for_agent") else None
        if household is not None:
            status = next((item for item in all_household_statuses(world) if item.household_id == household.household_id), None)
            if status is not None and status.overcrowded_by > 0:
                negative = "Overcrowding"
    return positive, negative


def performance_rows(world, renderer_metrics: dict[str, object]) -> list[tuple[str, object]]:
    active_agents = len([agent for agent in world.agents if getattr(agent, "alive", False)])
    cached_paths = sum(1 for agent in world.living_agents() if getattr(agent, "current_path", None))
    return [
        ("Population", len(world.living_agents())),
        ("Active Agents", active_agents),
        ("Simulation Tick Time", f"{getattr(world, 'last_tick_ms', 0.0):.2f} ms"),
        ("Render Tick Time", f"{float(renderer_metrics.get('last_render_ms', 0.0)):.2f} ms"),
        ("Current FPS", f"{float(renderer_metrics.get('fps', 0.0)):.1f}"),
        ("Path Requests", getattr(world, "pathfinding_calls", 0)),
        ("Cached Paths", cached_paths),
    ]


def format_counter(counter: Counter) -> str:
    if not counter:
        return "None"
    return " ".join(f"{key}:{counter[key]}" for key in sorted(counter))


def format_generation_counter(counter: Counter) -> str:
    if not counter:
        return "None"
    return " ".join(f"G{key}:{counter[key]}" for key in sorted(counter))
