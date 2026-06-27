from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.config import (
    HOUSE_TILE_CAPACITY,
    HOUSEHOLD_HOMELESS_BUILD_SCORE,
    HOUSEHOLD_OVERCROWDING_BUILD_SCORE,
    HOUSEHOLD_SPLIT_BUILD_SCORE,
    MAX_HOUSE_TILES_PER_HOUSEHOLD,
)
from src.lifecycle import ADULT, OLDER_ADULT, YOUNG_ADULT
from src.social_memory import villager_key

if TYPE_CHECKING:
    from src.agent import Agent
    from src.settlement import Home, Household
    from src.world import World


HOUSEHOLD_SPLIT_STAGES = {YOUNG_ADULT, ADULT, OLDER_ADULT}


@dataclass(frozen=True)
class HouseholdResidentialStatus:
    household_id: str
    occupants: int
    capacity: int
    house_tiles: int
    overcrowded_by: int
    at_max_size: bool
    homeless: bool
    expansion_site: tuple[int, int] | None = None
    wants_split: bool = False


@dataclass(frozen=True)
class ResidentialDemand:
    household_id: str | None
    demand_type: str
    score: float
    build_site: tuple[int, int] | None = None


@dataclass(frozen=True)
class ResidentialDiagnostics:
    overcrowded_households: int = 0
    homeless_households: int = 0
    household_split_candidates: int = 0
    expansion_candidates: int = 0
    total_house_tiles: int = 0
    total_house_capacity: int = 0


def household_homes(world: World, household: Household | None) -> list[Home]:
    settlement = getattr(world, "settlement", None)
    if settlement is None or household is None:
        return []

    homes = []
    for home in settlement.homes:
        if (
            home.household_id == household.household_id
            or home.home_id == household.home_id
            or home.home_id == household.home_building_id
        ):
            homes.append(home)
    return homes


def household_occupants(world: World, household: Household | None) -> list[Agent]:
    if household is None:
        return []
    member_ids = set(household.member_ids)
    return [
        agent
        for agent in world.living_agents()
        if (agent.agent_id or agent.name) in member_ids or getattr(agent, "household_id", None) == household.household_id
    ]


def household_capacity(world: World, household: Household | None) -> int:
    return len(household_homes(world, household)) * HOUSE_TILE_CAPACITY


def household_status(world: World, household: Household) -> HouseholdResidentialStatus:
    homes = household_homes(world, household)
    occupants = len(household_occupants(world, household))
    capacity = len(homes) * HOUSE_TILE_CAPACITY
    house_tiles = len(homes)
    expansion_site = None
    if 0 < house_tiles < MAX_HOUSE_TILES_PER_HOUSEHOLD:
        expansion_site = expansion_site_for_household(world, household)

    return HouseholdResidentialStatus(
        household_id=household.household_id,
        occupants=occupants,
        capacity=capacity,
        house_tiles=house_tiles,
        overcrowded_by=max(0, occupants - capacity),
        at_max_size=house_tiles >= MAX_HOUSE_TILES_PER_HOUSEHOLD,
        homeless=house_tiles == 0,
        expansion_site=expansion_site,
        wants_split=household_split_candidate_count(world, household) > 0,
    )


def all_household_statuses(world: World) -> list[HouseholdResidentialStatus]:
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return []
    return [household_status(world, household) for household in settlement.households]


def residential_demand(world: World) -> ResidentialDemand | None:
    statuses = all_household_statuses(world)
    if not statuses:
        return None

    homeless = [status for status in statuses if status.homeless]
    if homeless:
        status = max(homeless, key=lambda item: item.occupants)
        return ResidentialDemand(
            household_id=status.household_id,
            demand_type="new_house",
            score=HOUSEHOLD_HOMELESS_BUILD_SCORE + status.occupants * 4,
        )

    expandable = [
        status for status in statuses
        if status.overcrowded_by > 0 and not status.at_max_size and status.expansion_site is not None
    ]
    if expandable:
        status = max(expandable, key=lambda item: (item.overcrowded_by, item.occupants))
        return ResidentialDemand(
            household_id=status.household_id,
            demand_type="expand_house",
            score=HOUSEHOLD_OVERCROWDING_BUILD_SCORE + status.overcrowded_by * 12,
            build_site=status.expansion_site,
        )

    split_pressure = [
        status for status in statuses
        if status.overcrowded_by > 0 and (status.at_max_size or status.expansion_site is None) and status.wants_split
    ]
    if split_pressure:
        status = max(split_pressure, key=lambda item: (item.overcrowded_by, item.occupants))
        return ResidentialDemand(
            household_id=status.household_id,
            demand_type="split_household",
            score=HOUSEHOLD_SPLIT_BUILD_SCORE + status.overcrowded_by * 8,
        )

    return None


def update_residential_diagnostics(world: World):
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return

    statuses = all_household_statuses(world)
    settlement.overcrowded_households = sum(1 for status in statuses if status.overcrowded_by > 0)
    settlement.homeless_households = sum(1 for status in statuses if status.homeless)
    settlement.household_split_candidates = sum(1 for status in statuses if status.wants_split)
    settlement.house_expansion_candidates = sum(1 for status in statuses if status.expansion_site is not None)
    settlement.total_house_tiles = sum(status.house_tiles for status in statuses)
    settlement.total_house_capacity = sum(status.capacity for status in statuses)


def expansion_site_for_household(world: World, household: Household) -> tuple[int, int] | None:
    homes = household_homes(world, household)
    if not homes:
        return None

    candidates: list[tuple[int, int, int, tuple[int, int]]] = []
    for home in homes:
        for x, y in ((home.x, home.y - 1), (home.x + 1, home.y), (home.x, home.y + 1), (home.x - 1, home.y)):
            if not is_valid_house_expansion_site(world, x, y):
                continue
            distance = distance_to_primary_home(homes, x, y)
            candidates.append((distance, y, x, (x, y)))

    if not candidates:
        return None
    return min(candidates)[3]


def is_valid_house_expansion_site(world: World, x: int, y: int) -> bool:
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    if world.agent_at(x, y) is not None:
        return False
    tile = world.tile_at(x, y)
    if tile.kind != "grass":
        return False
    if world.stockpile_at(x, y) is not None or world.workshop_at(x, y) is not None:
        return False
    settlement = getattr(world, "settlement", None)
    if settlement is not None and (x, y) == (settlement.x, settlement.y):
        return False
    return True


def distance_to_primary_home(homes: list[Home], x: int, y: int) -> int:
    primary = homes[0]
    return abs(x - primary.x) + abs(y - primary.y)


def assign_house_tile_to_household(world: World, x: int, y: int, household: Household | None):
    from src.settlement import register_house

    home = register_house(world, x, y)
    if home is None:
        return None
    if household is not None:
        home.household_id = household.household_id
        if household.home_id is None:
            household.home_id = home.home_id
            household.home_building_id = home.home_id
    return home


def complete_residential_construction(world: World, x: int, y: int):
    settlement = getattr(world, "settlement", None)
    demand = residential_demand(world)
    household = settlement.household_for(demand.household_id) if settlement is not None and demand is not None else None
    world.tile_at(x, y).kind = "home"
    home = assign_house_tile_to_household(world, x, y, household if demand is not None and demand.demand_type != "split_household" else None)

    if demand is not None and demand.demand_type == "split_household":
        maybe_split_household_for_new_home(world, household, home)
    elif household is not None:
        for agent in household_occupants(world, household):
            if getattr(agent, "home_id", None) is None:
                world.add_agent_to_household(agent, household)

    update_residential_diagnostics(world)
    return home


def household_split_candidate_count(world: World, household: Household | None) -> int:
    if household is None:
        return 0
    candidates = household_split_candidates(world, household)
    return len(candidates)


def household_split_candidates(world: World, household: Household) -> list[tuple[Agent, Agent]]:
    agents_by_id = {villager_key(agent): agent for agent in household_occupants(world, household)}
    candidates: list[tuple[Agent, Agent]] = []
    seen: set[frozenset[str]] = set()
    for agent_id, agent in agents_by_id.items():
        partner_id = getattr(agent, "partner_id", None)
        if not partner_id or partner_id not in agents_by_id:
            continue
        partner = agents_by_id[partner_id]
        if getattr(partner, "partner_id", None) != agent_id:
            continue
        if not can_found_split_household(agent) or not can_found_split_household(partner):
            continue
        pair_key = frozenset((agent_id, partner_id))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        candidates.append((agent, partner))
    return candidates


def can_found_split_household(agent: Agent) -> bool:
    return getattr(agent, "alive", False) and getattr(agent, "lifecycle_stage", None) in HOUSEHOLD_SPLIT_STAGES


def maybe_split_household_for_new_home(world: World, source_household: Household | None, new_home) -> Household | None:
    settlement = getattr(world, "settlement", None)
    if settlement is None or source_household is None or new_home is None:
        return None

    candidates = household_split_candidates(world, source_household)
    if not candidates:
        return None

    first, second = candidates[0]
    household_id = next_household_id(settlement)
    household = type(source_household)(
        household_id=household_id,
        household_name=split_household_name(settlement, source_household),
        home_id=new_home.home_id,
        home_building_id=new_home.home_id,
        member_ids=[],
        founder_ids=[villager_key(first), villager_key(second)],
        founded_year=world.year,
        household_head=villager_key(first),
    )
    settlement.households.append(household)
    new_home.household_id = household.household_id
    world.add_agent_to_household(first, household)
    world.add_agent_to_household(second, household)
    world.household_split_events_by_year = getattr(world, "household_split_events_by_year", {})
    world.household_split_events_by_year[world.year] = world.household_split_events_by_year.get(world.year, 0) + 1
    record_household_split_history(world, source_household, household, first, second)
    return household


def next_household_id(settlement) -> str:
    existing = {household.household_id for household in settlement.households}
    index = len(existing)
    while f"household-{index}" in existing:
        index += 1
    return f"household-{index}"


def split_household_name(settlement, source_household: Household) -> str:
    base = source_household.household_name.split()[0] if source_household.household_name else "New"
    existing = {household.household_name for household in settlement.households}
    index = 2
    name = f"{base} Hearth {index}"
    while name in existing:
        index += 1
        name = f"{base} Hearth {index}"
    return name


def record_household_split_history(world: World, source_household: Household, new_household: Household, first: Agent, second: Agent):
    from src.generations import SUCCESSION

    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=SUCCESSION,
        title="Household Divides",
        description=(
            f"{first.name} and {second.name} established {new_household.household_name}, "
            f"a new home grown from {source_household.household_name}."
        ),
    )
