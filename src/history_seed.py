from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.scenarios import scenario_for_key
from src.world_history import ENVIRONMENT, HOUSEHOLD, LOCAL_STORY, MYSTERY, POPULATION, SETTLEMENT, WORKPLACE
from src.workplace import FARM, STORAGE, VILLAGE_CENTER, WORKSHOP

if TYPE_CHECKING:
    from src.world import World


def seed_starting_chronicle(world: World):
    settlement = getattr(world, "settlement", None)
    if settlement is None or world.history.count() > 0:
        return

    rng = random.Random(f"{world.seed}|starting-chronicle")
    scenario = scenario_for_key(getattr(settlement, "scenario_key", None))
    founding_year = settlement_foundation_year(world)

    record_settlement_history(world, founding_year)
    record_household_history(world, founding_year, household_limit_for_scenario(scenario))
    record_workplace_history(world, founding_year)
    record_population_milestones(world, founding_year)
    record_environmental_history(world, founding_year, rng, scenario.environmental_event_count)
    record_local_stories(world, founding_year, rng, scenario.local_story_count)
    record_mystery(world, founding_year, rng, scenario.mystery_count)


def settlement_foundation_year(world: World) -> int:
    settlement = world.settlement
    if settlement is None:
        return 1
    age_years = getattr(settlement, "age_years", 0)
    if age_years <= 0 and settlement.households:
        age_years = max((household.established_years for household in settlement.households), default=0)
    return min(1, world.year - max(1, age_years))


def record_settlement_history(world: World, founding_year: int):
    settlement = world.settlement
    home_count = len(settlement.homes)
    world.history.record(
        day=1,
        year=founding_year,
        season=settlement.founded_season,
        category=SETTLEMENT,
        title="Settlement Founded",
        description=f"{settlement.name} was founded around a central hearth and a reliable patch of open ground.",
    )
    if home_count:
        world.history.record(
            day=8,
            year=min(1, founding_year + 1),
            season="Spring",
            category=SETTLEMENT,
            title="First Homes Completed",
            description=f"The first cluster of {home_count} homes gave {settlement.name} its shape.",
        )
    if settlement.stockpiles:
        world.history.record(
            day=14,
            year=min(1, founding_year + 1),
            season="Summer",
            category=SETTLEMENT,
            title="Storage Established",
            description="A shared storage area was marked out so food, water, and wood could be kept near the village center.",
        )
    if settlement.local_water:
        world.history.record(
            day=23,
            year=min(1, founding_year + 2),
            season="Summer",
            category=SETTLEMENT,
            title="Water Route Marked",
            description="Villagers settled on a regular route between the homes and a dependable water source.",
        )


def record_household_history(world: World, founding_year: int, limit: int = 3):
    settlement = world.settlement
    households = sorted(
        settlement.households,
        key=lambda household: (-household.established_years, household.household_name),
    )
    for household in households[:limit]:
        year = min(1, household.founded_year)
        world.history.record(
            day=6,
            year=year,
            season="Spring",
            category=HOUSEHOLD,
            title="Household Founded",
            description=f"{household.household_name} took root in {settlement.name} and kept the same home for {household.established_years} years.",
        )
    if households:
        oldest = households[0]
        world.history.record(
            day=18,
            year=min(1, founding_year + max(1, oldest.established_years // 2)),
            season="Autumn",
            category=HOUSEHOLD,
            title="Old Hearth Remembered",
            description=f"{oldest.household_name} became known as one of the oldest households in the village.",
        )


def record_workplace_history(world: World, founding_year: int):
    settlement = world.settlement
    for workplace in settlement.workplaces:
        year = min(1, founding_year + workplace_year_offset(workplace.workplace_type))
        world.history.record(
            day=workplace_day(workplace.workplace_type),
            year=year,
            season=workplace_season(workplace.workplace_type),
            category=WORKPLACE,
            title=workplace_title(workplace.workplace_type),
            description=workplace_description(workplace.workplace_type, settlement.name, len(workplace.assigned_workers)),
        )


def record_population_milestones(world: World, founding_year: int):
    population = len(world.living_agents()) or world.settlement.population
    for milestone in (10, 20, 30, 40, 50):
        if population < milestone:
            continue
        year = min(1, founding_year + max(1, milestone // 10))
        world.history.record(
            day=milestone % 28 + 1,
            year=year,
            season="Spring" if milestone <= 20 else "Autumn",
            category=POPULATION,
            title=f"Population Reached {milestone}",
            description=f"The village counted {milestone} living souls and began to feel less like a camp.",
        )


def record_environmental_history(world: World, founding_year: int, rng: random.Random, limit: int = 2):
    options = [
        ("Harsh Winter", "A hard winter tested the stores, and households learned to keep closer to home."),
        ("Abundant Foraging", "One summer brought unusually generous wild food, and gatherers filled the storage area early."),
        ("Long Rains", "Several weeks of heavy rain softened the paths and sent villagers searching for drier crossings."),
        ("Thin Autumn", "A lean autumn taught the village to watch its food stores more carefully."),
    ]
    rng.shuffle(options)
    for index, (title, description) in enumerate(options[:max(0, limit)]):
        world.history.record(
            day=10 + index * 9,
            year=min(1, founding_year + 2 + index),
            season="Winter" if "Winter" in title else "Autumn",
            category=ENVIRONMENT,
            title=title,
            description=description,
        )


def record_local_stories(world: World, founding_year: int, rng: random.Random, limit: int = 3):
    agents = [agent for agent in world.living_agents() if getattr(agent, "personal_memories", None)]
    agents.sort(key=lambda agent: (-(agent.years_in_role), agent.name))
    for index, agent in enumerate(agents[:max(0, limit)]):
        memory = rng.choice(agent.personal_memories)
        world.history.record(
            day=12 + index * 4,
            year=min(1, founding_year + 3 + index),
            season=("Spring", "Summer", "Autumn")[index % 3],
            category=LOCAL_STORY,
            title="Local Story",
            description=f"{agent.name} of {world.settlement.name} is still remembered for this: {memory}",
        )


def record_mystery(world: World, founding_year: int, rng: random.Random, limit: int = 1):
    if limit <= 0:
        return

    mysteries = [
        "A pale light was seen above the western hills, and no one agreed how far away it was.",
        "The old well reflected stars at midday for one silent afternoon.",
        "Singing was heard from the forest on three windless nights.",
        "Strange footprints appeared after a storm and ended at the village path.",
        "A ring of frost remained around the village center until noon in midsummer.",
        "Several elders claimed the oldest path moved one step east after a moonless night.",
    ]
    rng.shuffle(mysteries)
    for index, mystery in enumerate(mysteries[:limit]):
        world.history.record(
            day=27 - min(index, 10),
            year=min(1, founding_year + rng.randint(1, 5 + index)),
            season=rng.choice(("Spring", "Summer", "Autumn", "Winter")),
            category=MYSTERY,
            title="Unexplained Sign",
            description=mystery,
        )


def household_limit_for_scenario(scenario) -> int:
    if scenario.age_years_range[1] <= 2:
        return 1
    if scenario.age_years_range[0] >= 50:
        return 5
    if scenario.age_years_range[0] >= 20:
        return 4
    return 3


def workplace_year_offset(workplace_type: str) -> int:
    return {
        VILLAGE_CENTER: 0,
        STORAGE: 1,
        FARM: 2,
        WORKSHOP: 3,
    }.get(workplace_type, 2)


def workplace_day(workplace_type: str) -> int:
    return {
        VILLAGE_CENTER: 2,
        STORAGE: 9,
        FARM: 16,
        WORKSHOP: 21,
    }.get(workplace_type, 12)


def workplace_season(workplace_type: str) -> str:
    return {
        VILLAGE_CENTER: "Spring",
        STORAGE: "Summer",
        FARM: "Spring",
        WORKSHOP: "Autumn",
    }.get(workplace_type, "Summer")


def workplace_title(workplace_type: str) -> str:
    return {
        VILLAGE_CENTER: "Village Center Marked",
        STORAGE: "Storage Expanded",
        FARM: "Field Ground Chosen",
        WORKSHOP: "Workshop Established",
    }.get(workplace_type, "Workplace Established")


def workplace_description(workplace_type: str, settlement_name: str, worker_count: int) -> str:
    worker_text = f"{worker_count} workers" if worker_count else "future workers"
    return {
        VILLAGE_CENTER: f"The center of {settlement_name} became the usual place for gathering, decisions, and evening talk.",
        STORAGE: f"The storage area grew into a daily meeting point for {worker_text}.",
        FARM: f"A field edge was kept clear so {settlement_name} could one day rely less on wild food.",
        WORKSHOP: f"A workshop space was established for repairs, tools, and patient hands.",
    }.get(workplace_type, f"A workplace was marked for {worker_text}.")
