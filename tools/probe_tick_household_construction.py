from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import TICKS_PER_DAY
from src.residential import all_household_statuses, residential_demand
from src.world import create_world


def run(seed: int, max_days: int) -> dict:
    world = create_world(seed=seed)
    first_demand = None
    first_split = None
    first_house_increase = None
    starting_homes = len(world.settlement.homes)

    for _ in range(max_days):
        for _ in range(TICKS_PER_DAY):
            world.update()
        demand = residential_demand(world)
        split_events = sum(getattr(world, "household_split_events_by_year", {}).values())
        homes = len(world.settlement.homes)
        if demand is not None and first_demand is None:
            first_demand = demand_row(world, demand)
        if split_events > 0 and first_split is None:
            first_split = {"day": world.day, "year": world.year, "split_events": split_events}
        if homes > starting_homes and first_house_increase is None:
            first_house_increase = {"day": world.day, "year": world.year, "homes": homes}
        if first_split is not None:
            break

    return {
        "seed": seed,
        "day": world.day,
        "year": world.year,
        "population": len(world.living_agents()),
        "births": getattr(world, "successful_births_total", 0),
        "deaths": len(getattr(world, "death_records", [])),
        "starting_homes": starting_homes,
        "homes": len(world.settlement.homes),
        "first_demand": first_demand,
        "first_house_increase": first_house_increase,
        "first_split": first_split,
        "split_events": sum(getattr(world, "household_split_events_by_year", {}).values()),
        "construction_progress_sites": len(getattr(world.settlement, "construction_progress", {})),
        "current_demand": demand_row(world, residential_demand(world)),
        "overcrowded_households": sum(1 for status in all_household_statuses(world) if status.overcrowded_by > 0),
    }


def demand_row(world, demand):
    if demand is None:
        return None
    return {
        "day": world.day,
        "year": world.year,
        "demand_type": demand.demand_type,
        "household_id": demand.household_id,
        "build_site": demand.build_site,
        "score": demand.score,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--max-days", type=int, default=1000)
    args = parser.parse_args()
    print(json.dumps(run(args.seed, args.max_days), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
