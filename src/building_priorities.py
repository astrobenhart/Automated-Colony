from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING

from src.config import (
    BUILDING_MATERIAL_SHELTER_WOOD_DISCOUNT,
    DESIRED_BUILDING_MATERIALS,
    DESIRED_WOOD_RESERVE,
    NEED_SCORE_HIGH_THRESHOLD,
    NEED_SCORE_LOW_THRESHOLD,
    NEED_SCORE_SWITCH_MARGIN,
    SHELTER_CAPACITY,
    SHELTER_CAPACITY_BUFFER,
)
from src.residential import residential_demand, update_residential_diagnostics

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


HOUSE = "home"
LEGACY_SHELTER = "shelter"
# Compatibility alias for older code/tests/imports. New construction uses houses.
SHELTER = HOUSE
WOOD = "wood"
MATERIALS = "materials"
HOUSE_WOOD_COST = 3
SHELTER_WOOD_COST = HOUSE_WOOD_COST


@dataclass(frozen=True)
class BuildingPriority:
    building_type: str
    existing_count: int
    needed_count: int
    wood_cost: int
    target_household_id: str | None = None
    demand_type: str | None = None
    build_site: tuple[int, int] | None = None

    @property
    def missing_count(self) -> int:
        return max(0, self.needed_count - self.existing_count)

    @property
    def wood_needed(self) -> int:
        return self.missing_count * self.wood_cost


def housing_structures(world: World) -> int:
    return world.count_tiles(HOUSE) + world.count_tiles(LEGACY_SHELTER)


def housing_capacity(world: World) -> int:
    return housing_structures(world) * SHELTER_CAPACITY


def needed_houses(world: World) -> int:
    current_houses = housing_structures(world)
    demand = residential_demand(world)
    if demand is not None:
        return current_houses + 1
    living_count = len(world.living_agents())
    if living_count == 0:
        return 0
    return max(current_houses, ceil(living_count / SHELTER_CAPACITY))


def needed_shelters(world: World) -> int:
    """Compatibility alias for older callers; new planning treats these as houses."""
    return needed_houses(world)


def highest_priority(world: World) -> BuildingPriority | None:
    update_settlement_needs(world)

    existing_houses = housing_structures(world)
    demand = residential_demand(world)
    required_houses = existing_houses + 1 if demand is not None else needed_houses(world)

    if existing_houses < required_houses:
        return BuildingPriority(
            building_type=SHELTER,
            existing_count=existing_houses,
            needed_count=required_houses,
            wood_cost=SHELTER_WOOD_COST,
            target_household_id=demand.household_id if demand is not None else None,
            demand_type=demand.demand_type if demand is not None else "new_house",
            build_site=demand.build_site if demand is not None else None,
        )

    return None


def needs_shelter(world: World) -> bool:
    priority = highest_priority(world)
    return priority is not None and priority.building_type == SHELTER


def needs_house(world: World) -> bool:
    return needs_shelter(world)


def should_gather_wood_for_construction(agent: Agent, world: World) -> bool:
    update_settlement_needs(world)
    settlement = world.settlement
    if settlement is None:
        priority = highest_priority(world)
        return priority is not None and priority.building_type == SHELTER and agent.wood < shelter_wood_cost_for_agent(agent, world)
    return settlement.top_need in (SHELTER, WOOD) and agent.wood < shelter_wood_cost_for_agent(agent, world)


def should_build_shelter(agent: Agent, world: World) -> bool:
    priority = highest_priority(world)
    if priority is None or priority.building_type != SHELTER:
        return False
    return agent.wood >= shelter_wood_cost_for_agent(agent, world)


def shelter_wood_cost_for_agent(agent: Agent, world: World) -> int:
    if world.colony_storage.building_materials <= 0:
        return SHELTER_WOOD_COST
    return max(1, SHELTER_WOOD_COST - BUILDING_MATERIAL_SHELTER_WOOD_DISCOUNT)


def update_settlement_needs(world: World, force: bool = False):
    settlement = world.settlement
    if settlement is None:
        return
    if not force and settlement.need_updated_day == world.day:
        return

    scores = settlement_need_scores(world)
    settlement.need_scores = scores
    settlement.top_need = stable_top_need(settlement.top_need, scores)
    update_residential_diagnostics(world)
    settlement.need_updated_day = world.day


def settlement_need_scores(world: World) -> dict[str, float]:
    return {
        SHELTER: shelter_need_score(world),
        WOOD: wood_need_score(world),
        MATERIALS: materials_need_score(world),
    }


def shelter_need_score(world: World) -> float:
    living = len(world.living_agents())
    capacity = housing_capacity(world)
    existing_houses = housing_structures(world)
    required_houses = needed_houses(world)
    missing_houses = max(0, required_houses - existing_houses)
    demand = residential_demand(world)

    if demand is not None:
        score = demand.score + max(0, living - capacity) * 5
    elif missing_houses > 0:
        score = 70 + missing_houses * 20 + max(0, living - capacity) * 5
    elif capacity - living < SHELTER_CAPACITY_BUFFER:
        score = 25
    else:
        score = 0

    if world.season == "Winter" and capacity - living < SHELTER_CAPACITY_BUFFER + 1:
        score += 10
    return float(score)


def wood_need_score(world: World) -> float:
    stored_wood = world.colony_storage.wood
    stored_materials = world.colony_storage.building_materials
    missing_houses = 1 if residential_demand(world) is not None else 0
    workshop_exists = world.workshop_at_anywhere()

    score = max(0, DESIRED_WOOD_RESERVE - stored_wood) * 5
    if missing_houses > 0:
        construction_need = missing_houses * SHELTER_WOOD_COST
        if stored_wood + stored_materials < construction_need:
            score += 45
        else:
            score += 15
    if workshop_exists and stored_materials < DESIRED_BUILDING_MATERIALS and stored_wood <= 0:
        score += 20
    return float(score)


def materials_need_score(world: World) -> float:
    if not world.workshop_at_anywhere():
        return 0.0

    stored_wood = world.colony_storage.wood
    stored_materials = world.colony_storage.building_materials
    if stored_materials >= DESIRED_BUILDING_MATERIALS or stored_wood <= 0:
        return 0.0

    missing_houses = 1 if residential_demand(world) is not None else 0
    score = (DESIRED_BUILDING_MATERIALS - stored_materials) * 10
    score += 25 if missing_houses > 0 else 10
    return float(score)


def stable_top_need(current_need: str | None, scores: dict[str, float]) -> str | None:
    top_need, top_score = max(scores.items(), key=lambda item: item[1])
    if top_score < NEED_SCORE_LOW_THRESHOLD:
        return None
    if current_need in scores and scores[current_need] >= NEED_SCORE_LOW_THRESHOLD:
        if top_need != current_need and top_score < scores[current_need] + NEED_SCORE_SWITCH_MARGIN:
            return current_need
    if top_score >= NEED_SCORE_HIGH_THRESHOLD:
        return top_need
    return current_need if current_need in scores and scores[current_need] >= NEED_SCORE_LOW_THRESHOLD else top_need


def should_produce_building_materials(world: World) -> bool:
    update_settlement_needs(world)
    settlement = world.settlement
    if settlement is None:
        return False
    if world.colony_storage.building_materials >= DESIRED_BUILDING_MATERIALS:
        return False
    return settlement.top_need == MATERIALS
