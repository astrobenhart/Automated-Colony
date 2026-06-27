from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import os
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DAYS_PER_SEASON, SEASONS
from src.generations import BIRTH, FAMILY, SUCCESSION
from src.residential import all_household_statuses
from src.simulation_runner import DAYS_PER_YEAR, SimulationRunner
from src.world import create_world

DAYS_PER_YEAR = DAYS_PER_SEASON * len(SEASONS)


@dataclass
class ValidationCollector:
    snapshot_interval_years: int = 5
    daily_populations: list[int] = field(default_factory=list)
    yearly_snapshots: list[dict] = field(default_factory=list)
    stalls: int = 0
    previous_day: int | None = None
    previous_homes: int = 0
    previous_split_events: int = 0
    residential_construction_events: int = 0
    residential_expansion_events: int = 0
    split_home_events: int = 0
    active_residential_demand_days: int = 0

    def attach(self, world):
        self.previous_day = world.day
        self.previous_homes = len(world.settlement.homes)
        self.previous_split_events = sum(getattr(world, "household_split_events_by_year", {}).values())
        self.daily_populations.append(len(world.living_agents()))

    def on_day(self, world):
        if self.previous_day is not None and world.day <= self.previous_day:
            self.stalls += 1
        self.previous_day = world.day
        self.daily_populations.append(len(world.living_agents()))
        self.active_residential_demand_days += int(has_residential_demand(world))

        homes = len(world.settlement.homes)
        split_events = sum(getattr(world, "household_split_events_by_year", {}).values())
        home_delta = max(0, homes - self.previous_homes)
        split_delta = max(0, split_events - self.previous_split_events)
        if home_delta:
            self.residential_construction_events += home_delta
            self.split_home_events += min(home_delta, split_delta)
            self.residential_expansion_events += max(0, home_delta - split_delta)
        self.previous_homes = homes
        self.previous_split_events = split_events

        interval_days = max(1, self.snapshot_interval_years) * DAYS_PER_YEAR
        if world.day % interval_days == 0:
            self.yearly_snapshots.append(snapshot(world))


def run_validation(
    seed: int,
    years: int,
    *,
    mode: str = "validation",
    render_sample: bool = True,
    snapshot_interval_years: int = 5,
) -> dict:
    if mode == "accelerated":
        mode = "validation"
    if mode not in {"interactive", "headless", "validation"}:
        raise ValueError(f"Unknown validation mode: {mode}")

    world = create_world(seed=seed)
    start_population = len(world.living_agents())
    start_households = len(world.settlement.households)
    start_families = len(getattr(world, "families", {}))
    start_homes = len(world.settlement.homes)
    warnings: list[str] = []

    collector = ValidationCollector(snapshot_interval_years=snapshot_interval_years)
    collector.attach(world)
    runner = SimulationRunner(world, mode=mode, on_day=collector.on_day)
    runner_metrics = runner.run_years(years)

    renderer = renderer_metrics(world) if render_sample else {"frame_ms": None, "fps": None, "cold_frame_ms": None}

    living = world.living_agents()
    statuses = all_household_statuses(world)
    final_population = len(living)
    births = getattr(world, "successful_births_total", None)
    if births is None:
        births = len([entry for entry in world.history.entries if entry.category == BIRTH])
    family_entries = len([entry for entry in world.history.entries if entry.category == FAMILY])
    succession_entries = len([entry for entry in world.history.entries if entry.category == SUCCESSION])
    environmental_events = [entry for entry in world.history.entries if entry.category == "ENVIRONMENT"]
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
    household_splits = sum(getattr(world, "household_split_events_by_year", {}).values())
    household_successions = sum(getattr(world, "household_succession_events_by_year", {}).values())
    natural_deaths = sum(getattr(world, "natural_deaths_by_year", {}).values())

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
    if years >= 50 and collector.active_residential_demand_days > 0 and collector.residential_construction_events == 0:
        warnings.append("construction_deadlock")
    if years >= 50 and births > 0 and household_splits == 0:
        warnings.append("no_household_splits")
    if collector.stalls:
        warnings.append("day_stall")
    if world.history.count() == 0:
        warnings.append("chronicle_inactive")

    return {
        "seed": seed,
        "mode": mode,
        "update_path": "World.update",
        "target_years": years,
        "ticks_executed": runner_metrics.ticks_executed,
        "days_executed": runner_metrics.days_executed,
        "final_year": world.year,
        "final_day": world.day,
        "elapsed_seconds": round(runner_metrics.wall_clock_seconds, 3),
        "simulation_ticks_per_second": round(runner_metrics.ticks_per_second, 2),
        "simulation_days_per_second": round(runner_metrics.days_per_second, 3),
        "simulation_years_per_second": round(runner_metrics.years_per_second, 5),
        "estimated_interactive_speedup": round(runner_metrics.estimated_interactive_speedup, 2),
        "cpu_user_seconds": round(runner_metrics.cpu_user_seconds, 3) if runner_metrics.cpu_user_seconds is not None else None,
        "cpu_system_seconds": round(runner_metrics.cpu_system_seconds, 3) if runner_metrics.cpu_system_seconds is not None else None,
        "starting_population": start_population,
        "final_population": final_population,
        "min_population": min(collector.daily_populations),
        "max_population": max(collector.daily_populations),
        "average_population": round(statistics.mean(collector.daily_populations), 2),
        "births": births,
        "birth_attempts": getattr(world, "birth_attempts_total", 0),
        "death_records": len(world.death_records),
        "natural_deaths": natural_deaths,
        "generations_reached": max(max_generation, family_generation),
        "households_start": start_households,
        "households": len(world.settlement.households),
        "families_start": start_families,
        "families": len(world.families),
        "homes_start": start_homes,
        "homes": len(world.settlement.homes),
        "household_succession_events": household_successions,
        "household_split_events": household_splits,
        "residential_construction_events": collector.residential_construction_events,
        "residential_expansion_events": collector.residential_expansion_events,
        "split_home_events": collector.split_home_events,
        "active_residential_demand_days": collector.active_residential_demand_days,
        "renderer_frame_ms": renderer["frame_ms"],
        "renderer_fps": renderer["fps"],
        "renderer_cold_frame_ms": renderer["cold_frame_ms"],
        "peak_memory_mb": round(runner_metrics.peak_memory_mb, 2),
        "current_memory_mb": round(runner_metrics.current_memory_mb, 2),
        "chronicle_entries": world.history.count(),
        "birth_chronicle_entries": len([entry for entry in world.history.entries if entry.category == BIRTH]),
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
        "simulation_stalls": collector.stalls,
        "yearly_snapshots": collector.yearly_snapshots,
    }


def has_residential_demand(world) -> bool:
    from src.residential import residential_demand

    return residential_demand(world) is not None


def snapshot(world) -> dict:
    return {
        "year": world.year,
        "population": len(world.living_agents()),
        "births": getattr(world, "successful_births_total", 0),
        "deaths": len(world.death_records),
        "natural_deaths": sum(getattr(world, "natural_deaths_by_year", {}).values()),
        "food": world.colony_storage.food,
        "water": world.colony_storage.water,
        "households": len(world.settlement.households),
        "families": len(world.families),
        "homes": len(world.settlement.homes),
        "household_splits": sum(getattr(world, "household_split_events_by_year", {}).values()),
        "housing_capacity": sum(status.capacity for status in all_household_statuses(world)),
        "chronicle_entries": world.history.count(),
    }


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
    mean_frame = statistics.mean(frame_times)
    return {
        "frame_ms": round(mean_frame, 3),
        "fps": round(1000.0 / max(mean_frame, 0.001), 2),
        "cold_frame_ms": round(cold_frame_ms, 3),
    }


def run_validation_job(job: tuple[int, int, str, bool, int]) -> dict:
    seed, years, mode, render_sample, snapshot_interval_years = job
    return run_validation(
        seed,
        years,
        mode=mode,
        render_sample=render_sample,
        snapshot_interval_years=snapshot_interval_years,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run tick-faithful v0.8 release validation through SimulationRunner and World.update()."
    )
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--years", type=int, required=True)
    parser.add_argument(
        "--mode",
        choices=["interactive", "headless", "validation", "accelerated"],
        default="validation",
        help="All modes execute every World.update tick. validation/headless disable presentation overhead.",
    )
    parser.add_argument("--snapshot-interval-years", type=int, default=5)
    parser.add_argument("--no-render-sample", action="store_true")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Run independent seeds in parallel processes. Each seed still executes every World.update tick.",
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    jobs = [
        (seed, args.years, args.mode, not args.no_render_sample, args.snapshot_interval_years)
        for seed in args.seeds
    ]
    if args.workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(run_validation_job, jobs))
    else:
        results = [run_validation_job(job) for job in jobs]
    output = json.dumps(results, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
