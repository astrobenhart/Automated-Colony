ADULT = "Adult"
ELDER = "Elder"

LIFECYCLE_STAGES = (ADULT, ELDER)


def is_valid_lifecycle_stage(stage: str) -> bool:
    return stage in LIFECYCLE_STAGES


def lifecycle_stage_for_index(index: int) -> str:
    return ADULT if index % 10 < 8 else ELDER
