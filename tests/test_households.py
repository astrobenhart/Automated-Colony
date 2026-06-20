from src.social_memory import SocialMemoryEntry
from src.villager_inspection import villager_detail_sections
from src.world import create_world


def test_starting_villagers_belong_to_households():
    world = create_world(seed=171, agent_count=45)
    household_ids = {household.household_id for household in world.settlement.households}

    assert world.settlement.households
    assert all(agent.household_id in household_ids for agent in world.agents)
    assert all(agent.home_id is not None for agent in world.agents)


def test_households_group_multiple_villagers_as_village_units():
    world = create_world(seed=172, agent_count=45)
    households_with_members = [
        household
        for household in world.settlement.households
        if len(household.member_ids) > 1
    ]

    assert households_with_members
    for household in world.settlement.households:
        assert household.household_name
        assert household.home_id is not None
        assert household.founder_ids


def test_household_members_share_home_anchor_for_night_gathering():
    world = create_world(seed=175, agent_count=45)
    household = next(
        household
        for household in world.settlement.households
        if len(household.member_ids) > 1
    )
    members = [
        agent
        for agent in world.agents
        if (agent.agent_id or agent.name) in household.member_ids
    ]
    anchors = {(member.home_id, member.home_x, member.home_y) for member in members}

    assert anchors == {(household.home_id, members[0].home_x, members[0].home_y)}


def test_generational_placeholders_exist_without_family_logic():
    world = create_world(seed=173, agent_count=12)

    assert all(agent.parent_ids == [] for agent in world.agents)
    assert all(agent.child_ids == [] for agent in world.agents)
    assert all(agent.generation == 0 for agent in world.agents)


def test_villager_card_shows_household_home_members_and_relationships():
    world = create_world(seed=174, agent_count=12)
    agent = world.agents[0]
    household = world.household_for_agent(agent)
    member_names = [
        member.name
        for member in world.agents
        if (member.agent_id or member.name) in household.member_ids
    ]
    agent.social_memory["friend"] = SocialMemoryEntry("friend", "Mara", familiarity_score=30, last_seen_day=3)
    agent.social_memory["known"] = SocialMemoryEntry("known", "Tessa", familiarity_score=2, last_seen_day=3)

    sections = dict(villager_detail_sections(agent, world))

    assert ("Household", household.household_name) in sections["Household"]
    assert any(label == "Home" and agent.home_id in value for label, value in sections["Household"])
    assert any(label == "Members" and member_names[0] in value for label, value in sections["Household"])
    assert ("Friend", "Mara") in sections["Relationships"]
    assert ("Known", "Tessa") in sections["Relationships"]
