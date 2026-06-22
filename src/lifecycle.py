from __future__ import annotations

import random
from dataclasses import dataclass

YOUNG_ADULT = "Young Adult"
ADULT = "Adult"
OLDER_ADULT = "Older Adult"
ELDER = "Elder"

LIFECYCLE_STAGES = (YOUNG_ADULT, ADULT, OLDER_ADULT, ELDER)

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
    return stage in LIFECYCLE_STAGES


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


def demographic_profiles(count: int, seed: object | None = None) -> list[DemographicProfile]:
    if count <= 0:
        return []

    rng = random.Random(f"{seed}|demographics|{count}")
    stages = lifecycle_stage_distribution(count)
    rng.shuffle(stages)
    return [profile_for_stage(stage, rng) for stage in stages]


def lifecycle_stage_distribution(count: int) -> list[str]:
    if count <= 0:
        return []

    elder_count = 1 if count >= 10 else max(0, round(count * 0.05))
    young_count = max(1, round(count * 0.25))
    older_count = max(1, round(count * 0.18)) if count >= 6 else 0
    adult_count = count - young_count - older_count - elder_count
    if adult_count < 1:
        adult_count = 1
        young_count = max(0, young_count - 1)

    return (
        [YOUNG_ADULT] * young_count
        + [ADULT] * adult_count
        + [OLDER_ADULT] * older_count
        + [ELDER] * elder_count
    )


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
