from src.agent import Agent
from src.births import household_can_support_birth
from src.building_priorities import needed_shelters, shelter_need_score
from src.config import HOUSE_TILE_CAPACITY, MAX_HOUSE_TILES_PER_HOUSEHOLD
from src.partnerships import form_partnership
from src.residential import (
    expansion_site_for_household,
    household_capacity,
    household_status,
    residential_demand,
)
from src.tile import Tile
from src.world import create_world


def test_housing_demand_no_longer_includes_future_growth_reserve():
    world = create_world(seed=1301, agent_count=45)

    assert residential_demand(world) is None
    assert needed_shelters(world) == world.count_tiles("home") + world.count_tiles("shelter")


def test_household_capacity_comes_from_owned_house_tiles():
    world = create_world(seed=1302, agent_count=20)
    household = world.settlement.households[0]
    home = world.settlement.home_for_id(household.home_id)
    x, y = home.x + 1, home.y
    world.tile_at(x, y).kind = "home"
    extra_home = world.settlement.homes.append(type(home)(x, y, home_id="home-extra", household_id=household.household_id))

    assert extra_home is None
    assert household_capacity(world, household) == HOUSE_TILE_CAPACITY * 2


def test_overcrowding_creates_expansion_demand_with_orthogonal_site():
    world = create_world(seed=1303, agent_count=20)
    household = next(
        household for household in world.settlement.households
        if expansion_site_for_household(world, household) is not None
    )
    for index in range(HOUSE_TILE_CAPACITY + 1):
        agent = Agent(f"Extra {index}", household.home_id.count("e") + index, 0, agent_id=f"extra-{index}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)

    status = household_status(world, household)
    demand = residential_demand(world)
    site = expansion_site_for_household(world, household)
    home = world.settlement.home_for_id(household.home_id)

    assert status.overcrowded_by > 0
    assert demand is not None
    assert demand.demand_type == "expand_house"
    assert demand.build_site == site
    assert abs(site[0] - home.x) + abs(site[1] - home.y) == 1


def test_max_house_size_blocks_more_expansion_and_prefers_split_pressure():
    world = create_world(seed=1304, agent_count=20)
    household = next(
        household for household in world.settlement.households
        if expansion_site_for_household(world, household) is not None
    )
    home = world.settlement.home_for_id(household.home_id)
    for offset in range(1, MAX_HOUSE_TILES_PER_HOUSEHOLD):
        x, y = home.x + offset, home.y
        world.tile_at(x, y).kind = "home"
        world.settlement.homes.append(type(home)(x, y, home_id=f"extra-{offset}", household_id=household.household_id))

    members = [agent for agent in world.living_agents() if agent.household_id == household.household_id]
    while len(members) < 2:
        agent = Agent(f"Founder {len(members)}", home.x, home.y, agent_id=f"founder-{len(members)}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)
        members.append(agent)
    first, second = members[:2]
    form_partnership(world, first, second)
    for index in range(MAX_HOUSE_TILES_PER_HOUSEHOLD * HOUSE_TILE_CAPACITY + 1):
        agent = Agent(f"Crowd {index}", index, 0, agent_id=f"crowd-{index}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)

    status = household_status(world, household)
    demand = residential_demand(world)

    assert status.at_max_size
    assert status.expansion_site is None
    assert status.wants_split
    assert demand is not None
    assert demand.demand_type == "split_household"


def test_household_birth_can_create_manageable_overcrowding():
    world = create_world(seed=1305, agent_count=20)
    household = next(
        household for household in world.settlement.households
        if expansion_site_for_household(world, household) is not None
    )
    for index in range(HOUSE_TILE_CAPACITY):
        agent = Agent(f"Birth Room {index}", index, 0, agent_id=f"birth-room-{index}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)
    parent = next(agent for agent in world.living_agents() if agent.household_id == household.household_id)

    assert household_status(world, household).occupants >= HOUSE_TILE_CAPACITY
    assert household_can_support_birth(world, parent)
    assert shelter_need_score(world) > 0
