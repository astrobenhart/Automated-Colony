from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING

from src.config import SHELTER_CAPACITY

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


SHELTER = "shelter"
SHELTER_WOOD_COST = 3


@dataclass(frozen=True)
class BuildingPriority:
    building_type: str
    existing_count: int
    needed_count: int
    wood_cost: int

    @property
    def missing_count(self) -> int:
        return max(0, self.needed_count - self.existing_count)

    @property
    def wood_needed(self) -> int:
        return self.missing_count * self.wood_cost


def needed_shelters(world: World) -> int:
    living_count = len(world.living_agents())
    if living_count == 0:
        return 0
    return ceil(living_count / SHELTER_CAPACITY)


def highest_priority(world: World) -> BuildingPriority | None:
    existing_shelters = world.count_tiles(SHELTER)
    required_shelters = needed_shelters(world)

    if existing_shelters < required_shelters:
        return BuildingPriority(
            building_type=SHELTER,
            existing_count=existing_shelters,
            needed_count=required_shelters,
            wood_cost=SHELTER_WOOD_COST,
        )

    return None


def needs_shelter(world: World) -> bool:
    priority = highest_priority(world)
    return priority is not None and priority.building_type == SHELTER


def should_gather_wood_for_construction(agent: Agent, world: World) -> bool:
    priority = highest_priority(world)
    if priority is None:
        return False
    return priority.building_type == SHELTER and agent.wood < priority.wood_cost


def should_build_shelter(agent: Agent, world: World) -> bool:
    priority = highest_priority(world)
    if priority is None or priority.building_type != SHELTER:
        return False
    return agent.wood >= priority.wood_cost
