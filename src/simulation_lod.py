from __future__ import annotations

from dataclasses import dataclass


LOD_0_VISUAL = "LOD 0 Visual Systems"
LOD_1_TASKS = "LOD 1 Active Task Execution"
LOD_2_NEEDS = "LOD 2 Needs Systems"
LOD_3_SOCIAL = "LOD 3 Social Systems"
LOD_4_PLANNING = "LOD 4 Settlement Planning"
LOD_5_HISTORY = "LOD 5 Historical Systems"


@dataclass(frozen=True)
class SimulationLODTier:
    key: str
    name: str
    cadence: str
    systems: tuple[str, ...]


LOD_TIERS: tuple[SimulationLODTier, ...] = (
    SimulationLODTier(
        key="lod0",
        name=LOD_0_VISUAL,
        cadence="Every render frame / tick",
        systems=("movement interpolation", "animation state", "render feedback"),
    ),
    SimulationLODTier(
        key="lod1",
        name=LOD_1_TASKS,
        cadence="Every simulation tick for the active villager batch",
        systems=("walking", "hauling", "harvesting", "building", "eating", "sleeping", "workplace actions"),
    ),
    SimulationLODTier(
        key="lod2",
        name=LOD_2_NEEDS,
        cadence="Hourly",
        systems=("hunger", "thirst", "fatigue", "wildlife updates"),
    ),
    SimulationLODTier(
        key="lod3",
        name=LOD_3_SOCIAL,
        cadence="Daily",
        systems=("relationship growth", "household familiarity", "workplace familiarity", "influence peaks"),
    ),
    SimulationLODTier(
        key="lod4",
        name=LOD_4_PLANNING,
        cadence="Daily or event-driven",
        systems=("resource targets", "workforce balancing", "housing demand", "workplace demand", "ecology"),
    ),
    SimulationLODTier(
        key="lod5",
        name=LOD_5_HISTORY,
        cadence="Event-driven or daily cleanup",
        systems=("chronicle entries", "remembrance expiry", "demographic records", "future family history"),
    ),
)


@dataclass
class LODProfileStat:
    calls: int = 0
    total_seconds: float = 0.0
    last_seconds: float = 0.0

    @property
    def average_seconds(self) -> float:
        if self.calls <= 0:
            return 0.0
        return self.total_seconds / self.calls

    def record(self, seconds: float):
        self.calls += 1
        self.total_seconds += max(0.0, seconds)
        self.last_seconds = max(0.0, seconds)


def tier_names() -> tuple[str, ...]:
    return tuple(tier.name for tier in LOD_TIERS)
