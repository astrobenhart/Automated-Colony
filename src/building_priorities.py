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

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


SHELTER = "shelter"
WOOD = "wood"
MATERIALS = "materials"
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
    update_settlement_needs(world)

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
    settlement.need_updated_day = world.day


def settlement_need_scores(world: World) -> dict[str, float]:
    return {
        SHELTER: shelter_need_score(world),
        WOOD: wood_need_score(world),
        MATERIALS: materials_need_score(world),
    }


def shelter_need_score(world: World) -> float:
    living = len(world.living_agents())
    existing_shelters = world.count_tiles(SHELTER)
    capacity = existing_shelters * SHELTER_CAPACITY
    required_shelters = needed_shelters(world)
    missing_shelters = max(0, required_shelters - existing_shelters)

    if missing_shelters > 0:
        score = 70 + missing_shelters * 20 + max(0, living - capacity) * 5
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
    existing_shelters = world.count_tiles(SHELTER)
    missing_shelters = max(0, needed_shelters(world) - existing_shelters)
    workshop_exists = world.workshop_at_anywhere()

    score = max(0, DESIRED_WOOD_RESERVE - stored_wood) * 5
    if missing_shelters > 0:
        construction_need = missing_shelters * SHELTER_WOOD_COST
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

    existing_shelters = world.count_tiles(SHELTER)
    missing_shelters = max(0, needed_shelters(world) - existing_shelters)
    score = (DESIRED_BUILDING_MATERIALS - stored_materials) * 10
    score += 25 if missing_shelters > 0 else 10
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
