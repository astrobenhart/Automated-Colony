from __future__ import annotations

import random
from dataclasses import dataclass

from src.scenarios import ANCIENT_HAMLET, MATURE_SETTLEMENT, PIONEER_CAMP
from src.generations import (
    FUTURE_LIFE_STAGES,
    LIFE_STAGE_ADULT,
    LIFE_STAGE_CHILD,
    LIFE_STAGE_ELDER,
    LIFE_STAGE_OLDER_ADULT,
    LIFE_STAGE_YOUNG_ADULT,
)

CHILD = LIFE_STAGE_CHILD
YOUNG_ADULT = LIFE_STAGE_YOUNG_ADULT
ADULT = LIFE_STAGE_ADULT
OLDER_ADULT = LIFE_STAGE_OLDER_ADULT
ELDER = LIFE_STAGE_ELDER

LIFECYCLE_STAGES = (YOUNG_ADULT, ADULT, OLDER_ADULT, ELDER)
SUPPORTED_LIFECYCLE_STAGES = FUTURE_LIFE_STAGES

NOVICE = "Novice"
EXPERIENCED = "Experienced"
VETERAN = "Veteran"

EXPERIENCE_LEVELS = (NOVICE, EXPERIENCED, VETERAN)

AGE_RANGES = {
    YOUNG_ADULT: (18, 29),
    ADULT: (30, 49),
    OLDER_ADULT: (50, 64),
    ELDER: (65, 84),
}


@dataclass(frozen=True)
class DemographicProfile:
    age: int
    lifecycle_stage: str
    experience_level: str


def is_valid_lifecycle_stage(stage: str) -> bool:
    return stage in SUPPORTED_LIFECYCLE_STAGES


def is_valid_experience_level(level: str) -> bool:
    return level in EXPERIENCE_LEVELS


def lifecycle_stage_for_age(age: int) -> str:
    if age < AGE_RANGES[ADULT][0]:
        return YOUNG_ADULT
    if age < AGE_RANGES[OLDER_ADULT][0]:
        return ADULT
    if age < AGE_RANGES[ELDER][0]:
        return OLDER_ADULT
    return ELDER


def lifecycle_stage_for_index(index: int) -> str:
    return lifecycle_stage_for_age(age_for_index(index))


def age_for_index(index: int) -> int:
    cycle = (
        18, 22, 27, 31, 35,
        39, 43, 47, 52, 57,
        62, 68, 74, 29, 34,
        41, 49, 55, 60, 70,
    )
    return cycle[index % len(cycle)]


def demographic_profiles(
    count: int,
    seed: object | None = None,
    scenario_key: str | None = None,
) -> list[DemographicProfile]:
    if count <= 0:
        return []

    rng = random.Random(f"{seed}|demographics|{scenario_key}|{count}")
    stages = lifecycle_stage_distribution(count, scenario_key=scenario_key)
    rng.shuffle(stages)
    return [profile_for_stage(stage, rng) for stage in stages]


def lifecycle_stage_distribution(count: int, scenario_key: str | None = None) -> list[str]:
    if count <= 0:
        return []

    young_ratio, older_ratio, elder_ratio = lifecycle_ratios_for_scenario(scenario_key)
    elder_count = round(count * elder_ratio)
    if count >= 10 and elder_ratio > 0:
        elder_count = max(1, elder_count)
    young_count = max(1, round(count * young_ratio))
    older_count = max(1, round(count * older_ratio)) if count >= 6 and older_ratio > 0 else 0
    adult_count = count - young_count - older_count - elder_count
    if adult_count < 1:
        adult_count = 1
        young_count = max(0, young_count - 1)
    while young_count + adult_count + older_count + elder_count > count:
        if young_count > 1:
            young_count -= 1
        elif older_count > 0:
            older_count -= 1
        elif elder_count > 0:
            elder_count -= 1
        else:
            adult_count -= 1

    return (
        [YOUNG_ADULT] * young_count
        + [ADULT] * adult_count
        + [OLDER_ADULT] * older_count
        + [ELDER] * elder_count
    )


def lifecycle_ratios_for_scenario(scenario_key: str | None) -> tuple[float, float, float]:
    if scenario_key == PIONEER_CAMP:
        return 0.35, 0.08, 0.02
    if scenario_key == MATURE_SETTLEMENT:
        return 0.16, 0.25, 0.10
    if scenario_key == ANCIENT_HAMLET:
        return 0.12, 0.30, 0.15
    return 0.25, 0.18, 0.05


def profile_for_stage(stage: str, rng: random.Random) -> DemographicProfile:
    age = age_for_stage(stage, rng)
    return DemographicProfile(
        age=age,
        lifecycle_stage=stage,
        experience_level=experience_for_age(age, rng),
    )


def age_for_stage(stage: str, rng: random.Random) -> int:
    low, high = AGE_RANGES.get(stage, AGE_RANGES[ADULT])
    return rng.randint(low, high)


def experience_for_age(age: int, rng: random.Random) -> str:
    roll = rng.random()
    if age < 30:
        return NOVICE if roll < 0.72 else EXPERIENCED
    if age < 50:
        if roll < 0.22:
            return NOVICE
        if roll < 0.82:
            return EXPERIENCED
        return VETERAN
    if roll < 0.10:
        return NOVICE
    if roll < 0.62:
        return EXPERIENCED
    return VETERAN
