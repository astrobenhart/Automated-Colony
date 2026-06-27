from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.births import birth_candidates
from src.config import DAYS_PER_SEASON, MAX_HOUSE_TILES_PER_HOUSEHOLD, SEASONS
from src.lifecycle import ADULT, OLDER_ADULT, YOUNG_ADULT
from src.partnerships import partnership_candidates, partnership_score
from src.residential import all_household_statuses, household_occupants, household_split_candidates, residential_demand
from src.social_memory import villager_key
from src.world import create_world


DAYS_PER_YEAR = DAYS_PER_SEASON * len(SEASONS)
ADULT_STAGES = {YOUNG_ADULT, ADULT, OLDER_ADULT}


def run(seed: int, years: int) -> dict:
    world = create_world(seed=seed)
    yearly = []
    sampled_agents = {}

    for _ in range(years * DAYS_PER_YEAR):
        world.advance_day()
        track_samples(world, sampled_agents)
        if world.day_of_year == 1:
            yearly.append(snapshot(world))

    return {
        "seed": seed,
        "years": years,
        "final": snapshot(world),
        "maxima": maxima(yearly),
        "first_nonzero": first_nonzero(yearly),
        "yearly": yearly,
        "representative_timelines": representative_timelines(world, sampled_agents),
    }


def snapshot(world) -> dict:
    living = world.living_agents()
    living_by_id = {villager_key(agent): agent for agent in living}
    households = getattr(world.settlement, "households", []) if world.settlement else []
    statuses = all_household_statuses(world)
    demand = residential_demand(world)
    adult_children = [
        agent for agent in living
        if getattr(agent, "lifecycle_stage", None) in ADULT_STAGES and getattr(agent, "parent_ids", [])
    ]
    partnered_adults = [
        agent for agent in living
        if getattr(agent, "lifecycle_stage", None) in ADULT_STAGES and partner_for(agent, living_by_id) is not None
    ]
    partnered_adult_children = [agent for agent in partnered_adults if getattr(agent, "parent_ids", [])]
    partnered_with_parents = [
        agent for agent in partnered_adult_children
        if any(
            parent_id in living_by_id and getattr(living_by_id[parent_id], "household_id", None) == getattr(agent, "household_id", None)
            for parent_id in getattr(agent, "parent_ids", [])
        )
    ]
    split_pairs_by_household = {
        household.household_id: household_split_candidates(world, household)
        for household in households
    }
    split_pair_count = sum(len(pairs) for pairs in split_pairs_by_household.values())
    split_reason_counts = split_blocker_reasons(world, adult_children, living_by_id, statuses)

    return {
        "year": world.year,
        "day": world.day,
        "population": len(living),
        "births": getattr(world, "successful_births_total", 0),
        "birth_attempts": getattr(world, "birth_attempts_total", 0),
        "deaths": len(getattr(world, "death_records", [])),
        "adult_children": len(adult_children),
        "unpartnered_adult_children": sum(1 for agent in adult_children if partner_for(agent, living_by_id) is None),
        "partnered_adult_children": len(partnered_adult_children),
        "partnered_adults": len(partnered_adults),
        "partnered_adults_living_with_parents": len(partnered_with_parents),
        "partnership_candidates": len(partnership_candidates(world)),
        "best_unpartnered_adult_child_partnership_score": best_unpartnered_child_score(world, adult_children),
        "birth_candidates": len(birth_candidates(world)),
        "households": len(households),
        "overcrowded_households": sum(1 for status in statuses if status.overcrowded_by > 0),
        "households_above_max_capacity": sum(
            1 for status in statuses
            if status.overcrowded_by > 0 and status.house_tiles >= MAX_HOUSE_TILES_PER_HOUSEHOLD
        ),
        "households_can_expand": sum(
            1 for status in statuses
            if status.overcrowded_by > 0 and status.expansion_site is not None
        ),
        "eligible_household_split_pairs": split_pair_count,
        "split_household_demand": demand is not None and demand.demand_type == "split_household",
        "residential_demand_type": demand.demand_type if demand is not None else None,
        "residential_demand_household_id": demand.household_id if demand is not None else None,
        "building_priority": priority_row(world),
        "household_splits": sum(getattr(world, "household_split_events_by_year", {}).values()),
        "household_successions": sum(getattr(world, "household_succession_events_by_year", {}).values()),
        "housing_capacity": sum(status.capacity for status in statuses),
        "largest_household_occupants": max((status.occupants for status in statuses), default=0),
        "largest_household_capacity": max((status.capacity for status in statuses), default=0),
        "split_blockers": dict(split_reason_counts),
    }


def split_blocker_reasons(world, adult_children, living_by_id, statuses) -> Counter:
    status_by_household = {status.household_id: status for status in statuses}
    reasons = Counter()
    seen_pairs = set()
    for agent in adult_children:
        agent_id = villager_key(agent)
        partner = partner_for(agent, living_by_id)
        if partner is None:
            reasons["no_partner"] += 1
            continue
        pair_key = frozenset((agent_id, villager_key(partner)))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        if getattr(partner, "partner_id", None) != agent_id:
            reasons["partner_not_reciprocal"] += 1
            continue
        if getattr(partner, "household_id", None) != getattr(agent, "household_id", None):
            reasons["partner_not_in_same_household"] += 1
            continue
        status = status_by_household.get(getattr(agent, "household_id", None))
        if status is None:
            reasons["missing_household_status"] += 1
            continue
        if status.overcrowded_by <= 0:
            reasons["household_not_overcrowded"] += 1
            continue
        if not (status.at_max_size or status.expansion_site is None):
            reasons["household_expands_before_split"] += 1
            continue
        reasons["eligible"] += 1
    return reasons


def partner_for(agent, living_by_id):
    partner_id = getattr(agent, "partner_id", None)
    if not partner_id:
        return None
    return living_by_id.get(partner_id)


def best_unpartnered_child_score(world, adult_children) -> int:
    unpartnered = [agent for agent in adult_children if getattr(agent, "partner_id", None) is None]
    best = 0
    for index, first in enumerate(unpartnered):
        for second in unpartnered[index + 1:]:
            try:
                best = max(best, partnership_score(first, second, world))
            except Exception:
                pass
    return best


def priority_row(world):
    priority = world.building_priority()
    if priority is None:
        return None
    return {
        "building_type": priority.building_type,
        "demand_type": priority.demand_type,
        "target_household_id": priority.target_household_id,
        "missing_count": priority.missing_count,
        "build_site": priority.build_site,
    }


def maxima(yearly: list[dict]) -> dict:
    keys = (
        "adult_children",
        "partnered_adult_children",
        "partnered_adults_living_with_parents",
        "overcrowded_households",
        "households_can_expand",
        "eligible_household_split_pairs",
        "birth_candidates",
        "partnership_candidates",
        "best_unpartnered_adult_child_partnership_score",
    )
    return {key: max((row[key] for row in yearly), default=0) for key in keys}


def first_nonzero(yearly: list[dict]) -> dict:
    keys = (
        "adult_children",
        "partnered_adult_children",
        "overcrowded_households",
        "eligible_household_split_pairs",
        "split_household_demand",
        "birth_candidates",
        "partnership_candidates",
    )
    result = {}
    for key in keys:
        row = next((item for item in yearly if item[key]), None)
        result[key] = row["year"] if row else None
    return result


def track_samples(world, sampled_agents):
    for agent in world.living_agents():
        if len(sampled_agents) >= 8:
            break
        if not getattr(agent, "parent_ids", []):
            continue
        agent_id = villager_key(agent)
        if agent_id not in sampled_agents:
            sampled_agents[agent_id] = []
        timeline = sampled_agents[agent_id]
        if not timeline or timeline[-1]["year"] != world.year:
            timeline.append({
                "year": world.year,
                "age": getattr(agent, "age", 0),
                "stage": getattr(agent, "lifecycle_stage", None),
                "household_id": getattr(agent, "household_id", None),
                "partner_id": getattr(agent, "partner_id", None),
                "parent_ids": list(getattr(agent, "parent_ids", [])),
            })


def representative_timelines(world, sampled_agents):
    names = {villager_key(agent): agent.name for agent in world.agents}
    output = []
    for agent_id, timeline in list(sampled_agents.items())[:5]:
        output.append({
            "villager_id": agent_id,
            "name": names.get(agent_id, agent_id),
            "timeline": timeline[:30],
        })
    return output


def summarize(results: list[dict]) -> dict:
    final_rows = [result["final"] for result in results]
    blocker_totals = Counter()
    for row in final_rows:
        blocker_totals.update(row["split_blockers"])
    return {
        "seeds": [result["seed"] for result in results],
        "final_populations": [row["population"] for row in final_rows],
        "total_births": sum(row["births"] for row in final_rows),
        "total_deaths": sum(row["deaths"] for row in final_rows),
        "max_eligible_split_pairs": max((result["maxima"]["eligible_household_split_pairs"] for result in results), default=0),
        "max_overcrowded_households": max((result["maxima"]["overcrowded_households"] for result in results), default=0),
        "max_partnered_adult_children": max((result["maxima"]["partnered_adult_children"] for result in results), default=0),
        "max_adult_children": max((result["maxima"]["adult_children"] for result in results), default=0),
        "median_best_unpartnered_adult_child_score": statistics.median(
            [result["maxima"]["best_unpartnered_adult_child_partnership_score"] for result in results]
        ) if results else 0,
        "final_split_blockers": dict(blocker_totals),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    results = [run(seed, args.years) for seed in args.seeds]
    payload = {
        "summary": summarize(results),
        "runs": results,
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
