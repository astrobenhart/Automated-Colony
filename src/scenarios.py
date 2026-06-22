from __future__ import annotations

import random
from dataclasses import dataclass


PIONEER_CAMP = "pioneer_camp"
GROWING_VILLAGE = "growing_village"
MATURE_SETTLEMENT = "mature_settlement"
ANCIENT_HAMLET = "ancient_hamlet"
DEFAULT_SCENARIO_KEY = GROWING_VILLAGE


@dataclass(frozen=True)
class ScenarioReserves:
    food: int = 0
    water: int = 0
    wood: int = 0
    seeds: int | None = None


@dataclass(frozen=True)
class SettlementScenario:
    key: str
    label: str
    age_years_range: tuple[int, int]
    population_range: tuple[int, int]
    home_count_range: tuple[int, int]
    reserve: ScenarioReserves = ScenarioReserves()
    environmental_event_count: int = 2
    local_story_count: int = 3
    mystery_count: int = 1
    path_traffic_multiplier: float = 1.0
    social_depth: float = 1.0

    def age_years(self, seed: object) -> int:
        low, high = self.age_years_range
        rng = random.Random(f"{seed}|{self.key}|scenario-age")
        return rng.randint(low, high)

    def population(self, seed: object) -> int:
        low, high = self.population_range
        rng = random.Random(f"{seed}|{self.key}|scenario-population")
        return rng.randint(low, high)


SETTLEMENT_SCENARIOS: dict[str, SettlementScenario] = {
    PIONEER_CAMP: SettlementScenario(
        key=PIONEER_CAMP,
        label="Pioneer Camp",
        age_years_range=(0, 2),
        population_range=(12, 20),
        home_count_range=(4, 7),
        reserve=ScenarioReserves(food=3, water=3, wood=4, seeds=4),
        environmental_event_count=1,
        local_story_count=1,
        mystery_count=0,
        path_traffic_multiplier=0.45,
        social_depth=0.55,
    ),
    GROWING_VILLAGE: SettlementScenario(
        key=GROWING_VILLAGE,
        label="Growing Village",
        age_years_range=(5, 15),
        population_range=(30, 60),
        home_count_range=(8, 15),
        environmental_event_count=2,
        local_story_count=3,
        mystery_count=1,
        path_traffic_multiplier=1.0,
        social_depth=1.0,
    ),
    MATURE_SETTLEMENT: SettlementScenario(
        key=MATURE_SETTLEMENT,
        label="Mature Settlement",
        age_years_range=(20, 50),
        population_range=(45, 60),
        home_count_range=(14, 20),
        reserve=ScenarioReserves(food=18, water=15, wood=14, seeds=14),
        environmental_event_count=3,
        local_story_count=5,
        mystery_count=1,
        path_traffic_multiplier=1.35,
        social_depth=1.35,
    ),
    ANCIENT_HAMLET: SettlementScenario(
        key=ANCIENT_HAMLET,
        label="Ancient Hamlet",
        age_years_range=(50, 90),
        population_range=(35, 55),
        home_count_range=(12, 18),
        reserve=ScenarioReserves(food=12, water=12, wood=10, seeds=10),
        environmental_event_count=4,
        local_story_count=6,
        mystery_count=3,
        path_traffic_multiplier=1.70,
        social_depth=1.70,
    ),
}


def scenario_for_key(key: str | None) -> SettlementScenario:
    return SETTLEMENT_SCENARIOS.get(key or DEFAULT_SCENARIO_KEY, SETTLEMENT_SCENARIOS[DEFAULT_SCENARIO_KEY])


def starting_population_for_scenario(
    scenario: SettlementScenario,
    seed: object,
    explicit_count: int | None,
    default_count: int,
) -> int:
    if explicit_count is not None:
        return max(0, int(explicit_count))
    if scenario.key == DEFAULT_SCENARIO_KEY:
        return default_count
    return scenario.population(seed)
