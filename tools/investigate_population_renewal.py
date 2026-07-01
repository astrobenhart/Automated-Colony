from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import json
import os
import statistics
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.births import (
    BIRTH_DAILY_CHANCE,
    BIRTH_DAILY_CHANCE_CAP,
    BIRTH_FOOD_RESERVE_DAYS,
    BIRTH_MAX_DEPENDENT_CHILDREN_PER_HOUSEHOLD,
    BIRTH_MIN_CHILD_SPACING_YEARS,
    BIRTH_MIN_PARTNERSHIP_YEARS,
    BIRTH_PARENT_STAGES,
    BIRTH_SCORE_CHANCE_FACTOR,
    BIRTH_WATER_RESERVE_DAYS,
    birth_score,
    effective_birth_food,
    effective_birth_water,
    is_birth_parent,
    settlement_id,
)
from src.config import SETTLEMENT_FOOD_TARGET_DAYS, SETTLEMENT_WATER_TARGET_DAYS
from src.lifecycle import ADULT, CHILD, ELDER, OLDER_ADULT, YOUNG_ADULT
from src.partnerships import PARTNERSHIP_LIFE_STAGES, partnership_candidates
from src.residential import all_household_statuses
from src.simulation_runner import DAYS_PER_YEAR, SimulationRunner
from src.social_memory import villager_key
from src.world import create_world


GATES = (
    "partnered",
    "parent_age_eligible",
    "mutual_partnership",
    "partnership_duration_satisfied",
    "living_together",
    "settlement_member",
    "household_rules_satisfied",
    "housing_available",
    "dependent_child_cap_satisfied",
    "child_spacing_satisfied",
    "food_available",
    "water_available",
    "eligible_partnership",
)


@dataclass
class DecadeAccumulator:
    decade: int
    days: int = 0
    population_samples: list[int] = field(default_factory=list)
    children_samples: list[int] = field(default_factory=list)
    working_adults_samples: list[int] = field(default_factory=list)
    elders_samples: list[int] = field(default_factory=list)
    adult_age_samples: list[int] = field(default_factory=list)
    average_household_size_samples: list[float] = field(default_factory=list)
    housing_capacity_samples: list[int] = field(default_factory=list)
    food_samples: list[int] = field(default_factory=list)
    water_samples: list[int] = field(default_factory=list)
    household_samples: list[int] = field(default_factory=list)
    family_samples: list[int] = field(default_factory=list)
    partnership_samples: list[int] = field(default_factory=list)
    eligible_partnership_samples: list[int] = field(default_factory=list)
    gate_passes: Counter = field(default_factory=Counter)
    gate_failures: Counter = field(default_factory=Counter)
    first_failure: Counter = field(default_factory=Counter)
    score_samples: list[int] = field(default_factory=list)
    chance_samples: list[float] = field(default_factory=list)
    children_per_household_samples: list[float] = field(default_factory=list)
    children_per_partnership_samples: list[float] = field(default_factory=list)
    age_at_first_child_samples: list[int] = field(default_factory=list)
    generation_depth_samples: list[int] = field(default_factory=list)
    birth_attempts_start: int = 0
    births_start: int = 0
    deaths_start: int = 0
    splits_start: int = 0
    successions_start: int = 0
    homes_start: int = 0
    partnerships_start: int = 0
    birth_attempts_end: int = 0
    births_end: int = 0
    deaths_end: int = 0
    splits_end: int = 0
    successions_end: int = 0
    homes_end: int = 0
    partnerships_end: int = 0

    def begin(self, world):
        self.birth_attempts_start = getattr(world, "birth_attempts_total", 0)
        self.births_start = getattr(world, "successful_births_total", 0)
        self.deaths_start = sum(getattr(world, "natural_deaths_by_year", {}).values())
        self.splits_start = sum(getattr(world, "household_split_events_by_year", {}).values())
        self.successions_start = sum(getattr(world, "household_succession_events_by_year", {}).values())
        self.homes_start = len(world.settlement.homes)
        self.partnerships_start = partnership_count(world)

    def finish(self, world):
        self.birth_attempts_end = getattr(world, "birth_attempts_total", 0)
        self.births_end = getattr(world, "successful_births_total", 0)
        self.deaths_end = sum(getattr(world, "natural_deaths_by_year", {}).values())
        self.splits_end = sum(getattr(world, "household_split_events_by_year", {}).values())
        self.successions_end = sum(getattr(world, "household_succession_events_by_year", {}).values())
        self.homes_end = len(world.settlement.homes)
        self.partnerships_end = partnership_count(world)

    def add_day(self, world):
        self.days += 1
        living = world.living_agents()
        adults = [agent for agent in living if getattr(agent, "lifecycle_stage", None) != CHILD]
        working_adults = [agent for agent in living if getattr(agent, "lifecycle_stage", None) in {YOUNG_ADULT, ADULT, OLDER_ADULT}]
        elders = [agent for agent in living if getattr(agent, "lifecycle_stage", None) == ELDER]
        children = [agent for agent in living if getattr(agent, "lifecycle_stage", None) == CHILD]
        statuses = all_household_statuses(world)
        self.population_samples.append(len(living))
        self.children_samples.append(len(children))
        self.working_adults_samples.append(len(working_adults))
        self.elders_samples.append(len(elders))
        self.adult_age_samples.extend(getattr(agent, "age", 0) for agent in adults)
        self.average_household_size_samples.append(len(living) / max(1, len(world.settlement.households)))
        self.housing_capacity_samples.append(sum(status.capacity for status in statuses))
        self.food_samples.append(world.colony_storage.food)
        self.water_samples.append(world.colony_storage.water)
        self.household_samples.append(len(world.settlement.households))
        self.family_samples.append(len(world.families))
        self.partnership_samples.append(partnership_count(world))
        self.eligible_partnership_samples.append(len(partnership_candidates(world)))
        self.generation_depth_samples.append(max((getattr(agent, "generation", 0) for agent in living), default=0))
        self.children_per_household_samples.append(len(children) / max(1, len(world.settlement.households)))
        self.children_per_partnership_samples.append(len(children) / max(1, partnership_count(world)))
        self.age_at_first_child_samples.extend(parent_ages_at_first_child(world))

        for result in evaluate_partnered_pairs(world):
            for gate in GATES:
                if result["gates"][gate]:
                    self.gate_passes[gate] += 1
                else:
                    self.gate_failures[gate] += 1
            if result["first_failure"]:
                self.first_failure[result["first_failure"]] += 1
            if result["gates"]["eligible_partnership"]:
                self.score_samples.append(result["score"])
                self.chance_samples.append(result["chance"])

    def to_dict(self) -> dict:
        return {
            "decade": self.decade,
            "days": self.days,
            "population_avg": rounded_mean(self.population_samples),
            "population_min": min(self.population_samples) if self.population_samples else 0,
            "population_max": max(self.population_samples) if self.population_samples else 0,
            "children_avg": rounded_mean(self.children_samples),
            "working_adults_avg": rounded_mean(self.working_adults_samples),
            "elders_avg": rounded_mean(self.elders_samples),
            "adult_age_avg": rounded_mean(self.adult_age_samples),
            "adult_age_median": rounded_median(self.adult_age_samples),
            "age_distribution": dict(self.age_distribution_summary()),
            "births": self.births_end - self.births_start,
            "birth_attempts": self.birth_attempts_end - self.birth_attempts_start,
            "natural_deaths": self.deaths_end - self.deaths_start,
            "partnerships_avg": rounded_mean(self.partnership_samples),
            "partnerships_delta": self.partnerships_end - self.partnerships_start,
            "eligible_partnerships_avg": rounded_mean(self.eligible_partnership_samples),
            "households_avg": rounded_mean(self.household_samples),
            "families_avg": rounded_mean(self.family_samples),
            "household_splits": self.splits_end - self.splits_start,
            "household_successions": self.successions_end - self.successions_start,
            "residential_expansions": max(0, self.homes_end - self.homes_start),
            "housing_capacity_avg": rounded_mean(self.housing_capacity_samples),
            "average_household_size": rounded_mean(self.average_household_size_samples),
            "children_per_household": rounded_mean(self.children_per_household_samples),
            "children_per_partnership": rounded_mean(self.children_per_partnership_samples),
            "age_at_first_child_avg": rounded_mean(self.age_at_first_child_samples),
            "generation_depth_max": max(self.generation_depth_samples) if self.generation_depth_samples else 0,
            "food_avg": rounded_mean(self.food_samples),
            "water_avg": rounded_mean(self.water_samples),
            "eligible_birth_score_avg": rounded_mean(self.score_samples),
            "eligible_birth_chance_avg": round(statistics.mean(self.chance_samples), 5) if self.chance_samples else 0.0,
            "gate_breakdown": gate_breakdown(self.gate_passes, self.gate_failures),
            "first_failure_reasons": dict(self.first_failure),
        }

    def age_distribution_summary(self) -> Counter:
        buckets = Counter()
        for age in self.adult_age_samples:
            if age < 30:
                buckets["18-29"] += 1
            elif age < 50:
                buckets["30-49"] += 1
            elif age < 65:
                buckets["50-64"] += 1
            else:
                buckets["65+"] += 1
        return buckets


class InvestigationCollector:
    def __init__(self):
        self.decades: dict[int, DecadeAccumulator] = {}
        self.current_decade: int | None = None

    def attach(self, world):
        self.current_decade = decade_for_world(world)
        self.decades[self.current_decade] = DecadeAccumulator(self.current_decade)
        self.decades[self.current_decade].begin(world)

    def on_day(self, world):
        decade = decade_for_world(world)
        if self.current_decade != decade:
            if self.current_decade is not None:
                self.decades[self.current_decade].finish(world)
            self.current_decade = decade
            self.decades[decade] = DecadeAccumulator(decade)
            self.decades[decade].begin(world)
        self.decades[decade].add_day(world)

    def finish(self, world):
        if self.current_decade is not None:
            self.decades[self.current_decade].finish(world)

    def rows(self) -> list[dict]:
        return [self.decades[key].to_dict() for key in sorted(self.decades)]


def run_investigation(seed: int, years: int) -> dict:
    world = create_world(seed=seed)
    collector = InvestigationCollector()
    collector.attach(world)
    runner = SimulationRunner(world, mode="validation", on_day=collector.on_day)
    metrics = runner.run_years(years)
    collector.finish(world)
    return {
        "seed": seed,
        "years": years,
        "final_population": len(world.living_agents()),
        "births": getattr(world, "successful_births_total", 0),
        "birth_attempts": getattr(world, "birth_attempts_total", 0),
        "natural_deaths": sum(getattr(world, "natural_deaths_by_year", {}).values()),
        "household_splits": sum(getattr(world, "household_split_events_by_year", {}).values()),
        "households": len(world.settlement.households),
        "families": len(world.families),
        "homes": len(world.settlement.homes),
        "housing_capacity": sum(status.capacity for status in all_household_statuses(world)),
        "chronicle_entries": world.history.count(),
        "simulation_ticks_per_second": round(metrics.ticks_per_second, 2),
        "elapsed_seconds": round(metrics.wall_clock_seconds, 3),
        "peak_memory_mb": round(metrics.peak_memory_mb, 2),
        "decades": collector.rows(),
    }


def evaluate_partnered_pairs(world) -> list[dict]:
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    seen: set[frozenset[str]] = set()
    results = []
    for parent_a in living_by_id.values():
        partner_id = getattr(parent_a, "partner_id", None)
        if not partner_id or partner_id not in living_by_id:
            continue
        parent_b = living_by_id[partner_id]
        pair_key = frozenset((villager_key(parent_a), villager_key(parent_b)))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        results.append(evaluate_pair(world, parent_a, parent_b))
    return results


def evaluate_pair(world, parent_a, parent_b) -> dict:
    gates = {gate: False for gate in GATES}
    gates["partnered"] = True
    gates["parent_age_eligible"] = is_birth_parent(parent_a) and is_birth_parent(parent_b)
    gates["mutual_partnership"] = (
        getattr(parent_a, "partner_id", None) == villager_key(parent_b)
        and getattr(parent_b, "partner_id", None) == villager_key(parent_a)
    )
    gates["partnership_duration_satisfied"] = (
        getattr(parent_a, "partnership_duration", 0) >= BIRTH_MIN_PARTNERSHIP_YEARS
        and getattr(parent_b, "partnership_duration", 0) >= BIRTH_MIN_PARTNERSHIP_YEARS
    )
    gates["living_together"] = (
        getattr(parent_a, "household_id", None)
        and getattr(parent_a, "household_id", None) == getattr(parent_b, "household_id", None)
    )
    gates["settlement_member"] = (
        getattr(world, "settlement", None) is not None
        and settlement_id(parent_a) == settlement_id(parent_b)
        and settlement_id(parent_a) == world.settlement.settlement_id
    )
    gates["household_rules_satisfied"] = gates["living_together"] and bool(getattr(parent_a, "household_id", None))
    gates["housing_available"] = household_can_support_birth_detail(world, parent_a)["allowed"]
    cap_detail = dependent_child_cap_detail(world, parent_a)
    gates["dependent_child_cap_satisfied"] = cap_detail["allowed"]
    spacing_detail = child_spacing_detail(world, parent_a, parent_b)
    gates["child_spacing_satisfied"] = spacing_detail["allowed"]
    resources = resource_detail(world)
    gates["food_available"] = resources["food_available"]
    gates["water_available"] = resources["water_available"]
    gates["eligible_partnership"] = all(gates[gate] for gate in GATES if gate != "eligible_partnership")
    score = birth_score(world, parent_a, parent_b) if gates["eligible_partnership"] else 0
    chance = min(BIRTH_DAILY_CHANCE_CAP, BIRTH_DAILY_CHANCE + max(0, score - 60) * BIRTH_SCORE_CHANCE_FACTOR) if score else 0.0
    return {
        "pair": [getattr(parent_a, "name", ""), getattr(parent_b, "name", "")],
        "gates": gates,
        "first_failure": first_failed_gate(gates),
        "score": score,
        "chance": chance,
        "details": {
            "housing": household_can_support_birth_detail(world, parent_a),
            "dependent_cap": cap_detail,
            "spacing": spacing_detail,
            "resources": resources,
        },
    }


def household_can_support_birth_detail(world, parent_a) -> dict:
    from src.config import MAX_HOUSE_TILES_PER_HOUSEHOLD
    from src.residential import household_capacity, household_homes, household_occupants

    household = world.household_for_agent(parent_a)
    if household is None:
        return {"allowed": False, "reason": "no_household", "occupants": 0, "capacity": 0, "house_tiles": 0}
    occupants = len(household_occupants(world, household))
    capacity = household_capacity(world, household)
    house_tiles = len(household_homes(world, household))
    allowed = capacity > 0 and (occupants < capacity or house_tiles < MAX_HOUSE_TILES_PER_HOUSEHOLD)
    reason = "available" if allowed else "full_at_max_size"
    if capacity <= 0:
        reason = "no_capacity"
    return {"allowed": allowed, "reason": reason, "occupants": occupants, "capacity": capacity, "house_tiles": house_tiles}


def dependent_child_cap_detail(world, parent_a) -> dict:
    household_id = getattr(parent_a, "household_id", None)
    dependent_children = [
        agent
        for agent in world.living_agents()
        if getattr(agent, "household_id", None) == household_id and getattr(agent, "lifecycle_stage", None) == CHILD
    ]
    count = len(dependent_children)
    return {
        "allowed": count < BIRTH_MAX_DEPENDENT_CHILDREN_PER_HOUSEHOLD,
        "dependent_children": count,
        "cap": BIRTH_MAX_DEPENDENT_CHILDREN_PER_HOUSEHOLD,
    }


def child_spacing_detail(world, parent_a, parent_b) -> dict:
    household_id = getattr(parent_a, "household_id", None)
    parent_ids = {villager_key(parent_a), villager_key(parent_b)}
    shared_children = [
        child
        for child in world.living_agents()
        if (
            getattr(child, "household_id", None) == household_id
            and getattr(child, "lifecycle_stage", None) == CHILD
            and parent_ids & set(getattr(child, "parent_ids", []) or [])
        )
    ]
    if not shared_children:
        return {"allowed": True, "youngest_shared_child_age": None, "required_age": BIRTH_MIN_CHILD_SPACING_YEARS}
    youngest_age = min(getattr(child, "age", 0) for child in shared_children)
    return {
        "allowed": youngest_age >= BIRTH_MIN_CHILD_SPACING_YEARS,
        "youngest_shared_child_age": youngest_age,
        "required_age": BIRTH_MIN_CHILD_SPACING_YEARS,
    }


def resource_detail(world) -> dict:
    population = max(1, len(world.living_agents()))
    food_target = population * min(BIRTH_FOOD_RESERVE_DAYS, SETTLEMENT_FOOD_TARGET_DAYS)
    water_target = population * min(BIRTH_WATER_RESERVE_DAYS, SETTLEMENT_WATER_TARGET_DAYS)
    food = effective_birth_food(world, population)
    water = effective_birth_water(world, population)
    return {
        "food": food,
        "food_target": food_target,
        "food_available": food >= food_target,
        "water": water,
        "water_target": water_target,
        "water_available": water >= water_target,
    }


def first_failed_gate(gates: dict[str, bool]) -> str | None:
    for gate in GATES:
        if gate != "eligible_partnership" and not gates[gate]:
            return gate
    return None


def partnership_count(world) -> int:
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    pairs = set()
    for agent_id, agent in living_by_id.items():
        partner_id = getattr(agent, "partner_id", None)
        if partner_id in living_by_id:
            pairs.add(frozenset((agent_id, partner_id)))
    return len(pairs)


def parent_ages_at_first_child(world) -> list[int]:
    ages = []
    for agent in world.living_agents():
        children = getattr(agent, "child_ids", []) or getattr(agent, "children_ids", [])
        if not children:
            continue
        child_ages = [
            getattr(child, "age", None)
            for child in world.agents
            if villager_key(child) in set(children) and getattr(child, "age", None) is not None
        ]
        if not child_ages:
            continue
        oldest_child_age = max(child_ages)
        ages.append(max(0, getattr(agent, "age", 0) - oldest_child_age))
    return ages


def decade_for_world(world) -> int:
    return ((world.year - 1) // 10) * 10 + 1


def gate_breakdown(passes: Counter, failures: Counter) -> dict:
    rows = {}
    for gate in GATES:
        total = passes[gate] + failures[gate]
        rows[gate] = {
            "pass": passes[gate],
            "fail": failures[gate],
            "blocked_pct": round((failures[gate] / total) * 100, 2) if total else 0.0,
        }
    return rows


def rounded_mean(values) -> float:
    return round(statistics.mean(values), 2) if values else 0.0


def rounded_median(values) -> float:
    return round(statistics.median(values), 2) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--years", type=int, default=100)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_investigation(args.seed, args.years)
    output = json.dumps(result, indent=2, sort_keys=True)
    Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
