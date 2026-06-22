from src.social_bonds import social_bonds
from src.social_memory import relationship_category
from src.villager_inspection import villager_detail_sections
from src.world import create_world


def test_starting_villagers_have_established_role_and_routine_history():
    world = create_world(seed=301, agent_count=45)

    assert any(agent.years_in_role > 0 for agent in world.agents)
    assert any(agent.routine_age > 0 for agent in world.agents)
    assert all(agent.years_in_role <= max(0, agent.age - 18) for agent in world.agents)
    assert any(agent.personal_memories for agent in world.agents)


def test_household_history_seeds_relationship_strength():
    world = create_world(seed=302, agent_count=45)
    household = next(
        household
        for household in world.settlement.households
        if household.established_years >= 3 and len(household.member_ids) > 1
    )
    members = [
        agent
        for agent in world.agents
        if (agent.agent_id or agent.name) in household.member_ids
    ]
    first, second = members[:2]

    entry = first.social_memory[second.agent_id]

    assert first.household_familiarity == household.established_years
    assert entry.familiarity_score >= 10
    assert relationship_category(entry.familiarity_score) in {"Familiar", "Friend"}


def test_workplace_history_seeds_coworker_familiarity():
    world = create_world(seed=303, agent_count=45)
    workplace = next(
        workplace
        for workplace in world.settlement.workplaces
        if len(workplace.assigned_workers) > 1
    )
    workers = [
        agent
        for agent in world.agents
        if (agent.agent_id or agent.name) in workplace.assigned_workers
    ]
    first, second = workers[:2]

    assert first.workplace_id == workplace.workplace_id
    assert first.workplace_familiarity >= 0
    assert second.agent_id in first.social_memory


def test_starting_social_bonds_are_derived_from_seeded_history():
    world = create_world(seed=304, agent_count=45)
    bonded = [agent for agent in world.agents if social_bonds(agent)]

    assert bonded
    assert any(
        bond.label in {"Friend", "Close Friend", "Trusted Companion"}
        for agent in bonded
        for bond in social_bonds(agent)
    )


def test_villager_inspection_shows_starting_memories():
    world = create_world(seed=305, agent_count=45)
    agent = next(agent for agent in world.agents if agent.personal_memories)

    sections = dict(villager_detail_sections(agent, world))

    assert any(label == "Memory" for label, _ in sections["Memories"])
    assert ("Role Years", agent.years_in_role) in sections["Identity"]
