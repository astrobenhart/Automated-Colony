from __future__ import annotations

from dataclasses import asdict, dataclass, field

LIFE_STAGE_CHILD = "Child"
LIFE_STAGE_YOUNG_ADULT = "Young Adult"
LIFE_STAGE_ADULT = "Adult"
LIFE_STAGE_OLDER_ADULT = "Older Adult"
LIFE_STAGE_ELDER = "Elder"

FUTURE_LIFE_STAGES = (
    LIFE_STAGE_CHILD,
    LIFE_STAGE_YOUNG_ADULT,
    LIFE_STAGE_ADULT,
    LIFE_STAGE_OLDER_ADULT,
    LIFE_STAGE_ELDER,
)

RELATIONSHIP_ACQUAINTANCE = "acquaintance"
RELATIONSHIP_FRIEND = "friend"
RELATIONSHIP_HOUSEHOLD_MEMBER = "household_member"
RELATIONSHIP_PARENT = "parent"
RELATIONSHIP_CHILD = "child"
RELATIONSHIP_SIBLING = "sibling"
RELATIONSHIP_PARTNER = "partner"

FUTURE_RELATIONSHIP_TYPES = (
    RELATIONSHIP_ACQUAINTANCE,
    RELATIONSHIP_FRIEND,
    RELATIONSHIP_HOUSEHOLD_MEMBER,
    RELATIONSHIP_PARENT,
    RELATIONSHIP_CHILD,
    RELATIONSHIP_SIBLING,
    RELATIONSHIP_PARTNER,
)

MEMORY_PARENT = "parent"
MEMORY_CHILD = "child"
MEMORY_SIBLING = "sibling"
MEMORY_HOUSEHOLD_ELDER = "household_elder"
MEMORY_FAMILY_LOSS = "family_loss"

FUTURE_FAMILY_MEMORY_CATEGORIES = (
    MEMORY_PARENT,
    MEMORY_CHILD,
    MEMORY_SIBLING,
    MEMORY_HOUSEHOLD_ELDER,
    MEMORY_FAMILY_LOSS,
)

DEATH_OLD_AGE = "old_age"
DEATH_ILLNESS = "illness"
DEATH_ACCIDENT = "accident"
DEATH_MYSTERIOUS = "mysterious_event"

FUTURE_DEATH_CAUSES = (
    DEATH_OLD_AGE,
    DEATH_ILLNESS,
    DEATH_ACCIDENT,
    DEATH_MYSTERIOUS,
)

INHERITANCE_PERSONALITY = "personality"
INHERITANCE_WORK_PREFERENCE = "work_preference"
INHERITANCE_SOCIAL_TENDENCY = "social_tendency"
INHERITANCE_APPEARANCE = "appearance"

INHERITABLE_TRAIT_CATEGORIES = (
    INHERITANCE_PERSONALITY,
    INHERITANCE_WORK_PREFERENCE,
    INHERITANCE_SOCIAL_TENDENCY,
    INHERITANCE_APPEARANCE,
)

BIRTH = "BIRTH"
FAMILY = "FAMILY"
SUCCESSION = "SUCCESSION"


@dataclass
class FamilyLinks:
    mother_id: str | None = None
    father_id: str | None = None
    parent_ids: list[str] = field(default_factory=list)
    children_ids: list[str] = field(default_factory=list)
    sibling_ids: list[str] = field(default_factory=list)
    partner_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InheritanceProfile:
    personality_traits: list[str] = field(default_factory=list)
    work_preferences: list[str] = field(default_factory=list)
    social_tendencies: list[str] = field(default_factory=list)
    appearance_traits: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FamilyMemoryRecord:
    category: str
    subject_id: str | None = None
    description: str = ""
    year: int | None = None
    day: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LifecycleRecord:
    birth_year: int | None = None
    death_year: int | None = None
    birth_day: int | None = None
    death_day: int | None = None
    life_stage_history: list[tuple[int, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "birth_year": self.birth_year,
            "death_year": self.death_year,
            "birth_day": self.birth_day,
            "death_day": self.death_day,
            "life_stage_history": [
                {"year": year, "stage": stage}
                for year, stage in self.life_stage_history
            ],
        }


@dataclass
class HouseholdLineageRecord:
    household_id: str
    founder_ids: list[str] = field(default_factory=list)
    generation_count: int = 1
    historical_member_ids: list[str] = field(default_factory=list)
    succession_history: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
