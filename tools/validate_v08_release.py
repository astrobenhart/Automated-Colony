from __future__ import annotations

import argparse
import json
import os
import sys
import statistics
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.generations import BIRTH, FAMILY, SUCCESSION
from src.residential import all_household_statuses
from src.world import create_world

try:
    import psutil
except ImportError:  # pragma: no cover - optional diagnostics dependency
    psutil = None


DAYS_PER_YEAR = 80


def run_validation(seed: int, years: int, render_sample: bool = True) -> dict:
    start_wall = time.perf_counter()
    process = psutil.Process(os.getpid()) if psutil else None
    peak_memory_mb = memory_mb(process)
    world = create_world(seed=seed)
    start_population = len(world.living_agents())
    start_households = len(world.settlement.households)
    start_families = len(getattr(world, "families", {}))
    daily_populations = [start_population]
    yearly_snapshots = []
    warnings: list[str] = []
    stalls = 0
    previous_day = world.day

    for day_index in range(years * DAYS_PER_YEAR):
        world.advance_day()
        if world.day == previous_day:
            stalls += 1
        previous_day = world.day
        daily_populations.append(len(world.living_agents()))
        if (day_index + 1) % DAYS_PER_YEAR == 0:
            yearly_snapshots.append(snapshot(world))
            peak_memory_mb = max(peak_memory_mb, memory_mb(process))

    renderer = renderer_metrics(world) if render_sample else {"frame_ms": None, "fps": None, "cold_frame_ms": None}
    peak_memory_mb = max(peak_memory_mb, memory_mb(process))
    current_memory_mb = memory_mb(process)
    elapsed = time.perf_counter() - start_wall

    living = world.living_agents()
    statuses = all_household_statuses(world)
    final_population = len(living)
    births = len([entry for entry in world.history.entries if entry.category == BIRTH])
    family_entries = len([entry for entry in world.history.entries if entry.category == FAMILY])
    succession_entries = len([entry for entry in world.history.entries if entry.category == SUCCESSION])
    environmental_events = [
        entry
        for entry in world.history.entries
        if entry.category == "ENVIRONMENT"
    ]
    resource_trends = {
        "food": world.colony_storage.food,
        "water": world.colony_storage.water,
        "wood": world.colony_storage.wood,
        "local_food": len(getattr(world.settlement, "local_food", set())),
        "local_water": len(getattr(world.settlement, "local_water", set())),
        "farm_plots": len(world.settlement.farm_plots),
        "farm_ready_food": sum(farm.food for farm in world.settlement.farm_plots if farm.active),
    }
    max_generation = max((getattr(agent, "generation", 0) for agent in living), default=0)
    family_generation = max((family.generation_count for family in world.families.values()), default=0)
    housing_capacity = sum(status.capacity for status in statuses)
    overcrowded = sum(1 for status in statuses if status.overcrowded_by > 0)
    homeless = sum(1 for status in statuses if status.homeless)

    if final_population == 0:
        warnings.append("extinction")
    if final_population > start_population * 4:
        warnings.append("runaway_population")
    if final_population < max(3, start_population * 0.35):
        warnings.append("population_collapse")
    if births == 0 and years >= 50:
        warnings.append("birth_deadlock")
    if len(world.death_records) == 0 and years >= 50:
        warnings.append("no_deaths_recorded")
    if len(world.families) < start_families:
        warnings.append("family_count_decreased")
    if housing_capacity < final_population:
        warnings.append("housing_over_capacity")
    if world.colony_storage.water == 0 and len(getattr(world.settlement, "local_water", set())) == 0:
        warnings.append("water_collapse")
    if world.colony_storage.food == 0 and resource_trends["local_food"] == 0 and resource_trends["farm_ready_food"] == 0:
        warnings.append("food_collapse")
    if stalls:
        warnings.append("day_stall")

    return {
        "seed": seed,
        "target_years": years,
        "final_year": world.year,
        "final_day": world.day,
        "elapsed_seconds": round(elapsed, 3),
        "starting_population": start_population,
        "final_population": final_population,
        "min_population": min(daily_populations),
        "max_population": max(daily_populations),
        "average_population": round(statistics.mean(daily_populations), 2),
        "births": births,
        "death_records": len(world.death_records),
        "natural_deaths": sum(getattr(world, "natural_deaths_by_year", {}).values()),
        "generations_reached": max(max_generation, family_generation),
        "households_start": start_households,
        "households": len(world.settlement.households),
        "families_start": start_families,
        "families": len(world.families),
        "household_succession_events": sum(getattr(world, "household_succession_events_by_year", {}).values()),
        "household_split_events": sum(getattr(world, "household_split_events_by_year", {}).values()),
        "renderer_frame_ms": renderer["frame_ms"],
        "renderer_fps": renderer["fps"],
        "renderer_cold_frame_ms": renderer["cold_frame_ms"],
        "peak_memory_mb": round(peak_memory_mb, 2),
        "current_memory_mb": round(current_memory_mb, 2),
        "chronicle_entries": world.history.count(),
        "birth_chronicle_entries": births,
        "family_chronicle_entries": family_entries,
        "succession_chronicle_entries": succession_entries,
        "major_environmental_events": len(environmental_events),
        "settlement_status": getattr(world.settlement.carrying_capacity_report, "status", "Unknown"),
        "settlement_reason": getattr(world.settlement.carrying_capacity_report, "primary_reason", ""),
        "resource_trends": resource_trends,
        "housing_capacity": housing_capacity,
        "overcrowded_households": overcrowded,
        "homeless_households": homeless,
        "warnings": warnings,
        "simulation_stalls": stalls,
        "yearly_snapshots": yearly_snapshots,
    }


def snapshot(world) -> dict:
    return {
        "year": world.year,
        "population": len(world.living_agents()),
        "births": len([entry for entry in world.history.entries if entry.category == BIRTH]),
        "deaths": len(world.death_records),
        "food": world.colony_storage.food,
        "water": world.colony_storage.water,
        "households": len(world.settlement.households),
        "families": len(world.families),
    }


def memory_mb(process) -> float:
    if process is None:
        return 0.0
    return process.memory_info().rss / (1024 * 1024)


def renderer_metrics(world) -> dict:
    import pygame

    from src.renderer import PygameRenderer

    pygame.init()
    renderer = PygameRenderer(world)
    renderer.draw(paused=True, sim_speed=1)
    cold_frame_ms = renderer.last_render_ms
    frame_times = []
    for _ in range(10):
        renderer.draw(paused=True, sim_speed=1)
        frame_times.append(renderer.last_render_ms)
    pygame.quit()
    return {
        "frame_ms": round(statistics.mean(frame_times), 3),
        "fps": round(1000.0 / max(statistics.mean(frame_times), 0.001), 2),
        "cold_frame_ms": round(cold_frame_ms, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--years", type=int, required=True)
    parser.add_argument("--no-render-sample", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    results = [
        run_validation(seed, args.years, render_sample=not args.no_render_sample)
        for seed in args.seeds
    ]
    output = json.dumps(results, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
