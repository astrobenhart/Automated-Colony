from src.death_memory import record_death
from src.diagnostics import diagnostics_sections
from src.families import ensure_family_registry
from src.generations import FAMILY, SUCCESSION
from src.lifecycle import ELDER
from src.renewal import ensure_expected_lifespan, update_renewal
from src.residential import complete_residential_construction, expansion_site_for_household, household_status, residential_demand
from src.social_memory import villager_key
from src.world import create_world


def two_member_household_world(seed: int = 2301):
    world = create_world(seed=seed, agent_count=12)
    household = world.settlement.households[0]
    head = world.agents[0]
    successor = world.agents[1]
    world.add_agent_to_household(head, household)
    world.add_agent_to_household(successor, household)
    household.household_head = villager_key(head)
    head.partner_id = villager_key(successor)
    successor.partner_id = villager_key(head)
    return world, household, head, successor


def test_natural_aging_death_records_old_age_and_updates_year_counter(monkeypatch):
    world, _household, elder, _successor = two_member_household_world()
    elder.age = 96
    elder.lifecycle_stage = ELDER
    elder.expected_lifespan = 76
    monkeypatch.setattr("src.renewal.natural_death_daily_chance", lambda agent: 1.0 if agent is elder else 0.0)

    deaths = update_renewal(world)

    assert len(deaths) == 1
    assert not elder.alive
    assert world.death_records[-1].villager_id == villager_key(elder)
    assert world.death_records[-1].cause_of_death == "old age"
    assert world.natural_deaths_by_year[world.year] == 1


def test_household_head_succession_prefers_surviving_partner():
    world, household, head, successor = two_member_household_world()

    record_death(world, head, "old age")

    assert household.household_head == villager_key(successor)
    assert household.succession_history
    assert world.household_succession_events_by_year[world.year] == 1
    assert any(entry.category == SUCCESSION and successor.name in entry.description for entry in world.history.entries)


def test_family_persists_after_founder_death():
    world, _household, founder, successor = two_member_household_world()
    ensure_family_registry(world)
    successor.family_id = founder.family_id
    family = world.families[founder.family_id]
    family.add_member(villager_key(successor), alive=True, generation=getattr(successor, "generation", 0))

    record_death(world, founder, "old age")

    assert founder.family_id in world.families
    assert villager_key(founder) in family.deceased_member_ids
    assert villager_key(successor) in family.living_member_ids
    assert any(entry.category == FAMILY and "lost its founder" in entry.description for entry in world.history.entries)


def test_household_split_records_renewal_chronicle_entry():
    world = create_world(seed=2302, agent_count=20)
    household = next(
        household
        for household in world.settlement.households
        if expansion_site_for_household(world, household) is not None
    )
    home = world.settlement.home_for_id(household.home_id)
    from src.agent import Agent
    from src.config import HOUSE_TILE_CAPACITY, MAX_HOUSE_TILES_PER_HOUSEHOLD
    from src.partnerships import form_partnership

    for offset in range(1, MAX_HOUSE_TILES_PER_HOUSEHOLD):
        x, y = home.x + offset, home.y
        world.tile_at(x, y).kind = "home"
        world.settlement.homes.append(type(home)(x, y, home_id=f"renewal-extra-{offset}", household_id=household.household_id))
    members = [agent for agent in world.living_agents() if agent.household_id == household.household_id]
    while len(members) < 2:
        agent = Agent(f"Split {len(members)}", home.x, home.y, agent_id=f"split-{len(members)}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)
        members.append(agent)
    first, second = members[:2]
    form_partnership(world, first, second)
    for index in range(MAX_HOUSE_TILES_PER_HOUSEHOLD * HOUSE_TILE_CAPACITY + 1):
        agent = Agent(f"Crowd {index}", index, 0, agent_id=f"renewal-crowd-{index}")
        world.agents.append(agent)
        world.add_agent_to_household(agent, household)

    demand = residential_demand(world)
    assert demand is not None and demand.demand_type == "split_household"
    x, y = home.x, home.y + 1
    world.tile_at(x, y).kind = "grass"

    complete_residential_construction(world, x, y)

    assert world.household_split_events_by_year[world.year] == 1
    assert any(entry.category == SUCCESSION and entry.title == "Household Divides" for entry in world.history.entries)


def test_renewal_diagnostics_expose_age_death_generation_and_succession_data():
    world, _household, head, _successor = two_member_household_world()
    ensure_expected_lifespan(world, head)
    record_death(world, head, "old age")

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert "Age Distribution" in sections["Lifecycle"]
    assert "Expected Deaths This Year" in sections["Lifecycle"]
    assert "Generation Distribution" in sections["Lifecycle"]
    assert sections["Households"]["Succession Events This Year"] == 1
