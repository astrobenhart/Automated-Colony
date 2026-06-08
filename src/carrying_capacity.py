from __future__ import annotations

from dataclasses import dataclass, field

from src.config import SHELTER_CAPACITY


STABLE = "Stable"
FOOD_STRAINED = "Food Strained"
WATER_STRAINED = "Water Strained"
SHELTER_STRAINED = "Shelter Strained"
NO_SETTLEMENT = "No Settlement"


@dataclass(frozen=True)
class CarryingCapacityReport:
    population: int
    capacity: int
    status: str
    reason: str
    reason_lines: list[str] = field(default_factory=list)
    shelter_capacity: int = 0
    food_capacity: int = 0
    water_capacity: int = 0


def carrying_capacity_report(world) -> CarryingCapacityReport:
    settlement = world.settlement
    if settlement is None:
        return CarryingCapacityReport(
            population=len(world.living_agents()),
            capacity=0,
            status=NO_SETTLEMENT,
            reason="No settlement center has been founded.",
            reason_lines=["No settlement center has been founded."],
        )

    population = len(world.living_agents())
    shelter_capacity = _shelter_capacity(world)
    food_capacity = _food_capacity(world)
    water_capacity = _water_capacity(world)
    capacity = min(shelter_capacity, food_capacity, water_capacity)

    limiting_status, limiting_reason = _limiting_status(
        shelter_capacity=shelter_capacity,
        food_capacity=food_capacity,
        water_capacity=water_capacity,
    )
    if population <= capacity:
        status = STABLE
        reason = "Current shelter, food, and water can support the living population."
    else:
        status = limiting_status
        reason = limiting_reason

    reason_lines = _reason_lines(
        population=population,
        shelter_capacity=shelter_capacity,
        food_capacity=food_capacity,
        water_capacity=water_capacity,
        stored_food=world.colony_storage.food,
        local_food=len(settlement.local_food),
        ready_farm_food=sum(farm.food for farm in settlement.farm_plots if farm.active),
        farm_plots=len([farm for farm in settlement.farm_plots if farm.active]),
        local_water=len(settlement.local_water),
        shelters=world.count_tiles("shelter"),
    )

    return CarryingCapacityReport(
        population=population,
        capacity=capacity,
        status=status,
        reason=reason,
        reason_lines=reason_lines,
        shelter_capacity=shelter_capacity,
        food_capacity=food_capacity,
        water_capacity=water_capacity,
    )


def _shelter_capacity(world) -> int:
    return world.count_tiles("shelter") * SHELTER_CAPACITY


def _food_capacity(world) -> int:
    settlement = world.settlement
    if settlement is None:
        return 0
    stored_food = world.colony_storage.food
    local_food = len(settlement.local_food)
    ready_farm_food = sum(farm.food for farm in settlement.farm_plots if farm.active)
    active_farms = len([farm for farm in settlement.farm_plots if farm.active])

    storage_support = stored_food // 2
    wild_support = local_food
    farm_support = ready_farm_food + active_farms * 2
    return max(0, storage_support + wild_support + farm_support)


def _water_capacity(world) -> int:
    settlement = world.settlement
    if settlement is None:
        return 0
    return len(settlement.local_water) * 4


def _limiting_status(
    shelter_capacity: int,
    food_capacity: int,
    water_capacity: int,
) -> tuple[str, str]:
    limits = [
        (food_capacity, FOOD_STRAINED, "Food is the limiting factor."),
        (water_capacity, WATER_STRAINED, "Water access is the limiting factor."),
        (shelter_capacity, SHELTER_STRAINED, "Shelter space is the limiting factor."),
    ]
    _, status, reason = min(limits, key=lambda item: (item[0], item[1]))
    return status, reason


def _reason_lines(
    population: int,
    shelter_capacity: int,
    food_capacity: int,
    water_capacity: int,
    stored_food: int,
    local_food: int,
    ready_farm_food: int,
    farm_plots: int,
    local_water: int,
    shelters: int,
) -> list[str]:
    return [
        f"Population: {population}",
        f"Shelter: {shelter_capacity} capacity from {shelters} shelters",
        f"Food: {food_capacity} capacity from {stored_food} stored, {local_food} local, {ready_farm_food} farm-ready",
        f"Water: {water_capacity} capacity from {local_water} local water sources",
        f"Farms: {farm_plots} active plots",
    ]
