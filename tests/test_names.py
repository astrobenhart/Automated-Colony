from src.agent import Agent
from src.names import assign_persistent_name, is_placeholder_name, migrate_world_names
from src.settlement import Household, Settlement
from src.tile import Tile
from src.world import World, create_world


def test_assign_persistent_name_replaces_child_placeholder():
    child = Agent("Child 23", 1, 1, agent_id="child-23")

    assign_persistent_name(child, seed=44, key=child.agent_id)

    assert child.first_name
    assert child.surname
    assert child.name == f"{child.first_name} {child.surname}"
    assert not is_placeholder_name(child.name)
    assert "Child 23" not in child.name


def test_migration_preserves_existing_first_name_and_adds_surname():
    world = World(4, 4, seed=12)
    world.tiles = [[Tile("grass") for _ in range(4)] for _ in range(4)]
    agent = Agent("Ari", 1, 1, agent_id="ari")
    world.agents = [agent]

    changed = migrate_world_names(world)

    assert changed == 1
    assert agent.first_name == "Ari"
    assert agent.surname
    assert agent.name.startswith("Ari ")


def test_migration_is_stable_after_name_is_assigned():
    world = World(4, 4, seed=12)
    agent = Agent("Lily Ash", 1, 1, agent_id="lily")
    world.agents = [agent]

    assert migrate_world_names(world) == 0
    assert migrate_world_names(world) == 0
    assert agent.name == "Lily Ash"


def test_created_world_starts_with_persistent_villager_names():
    world = create_world(width=16, height=16, agent_count=4, seed=91)

    assert world.agents
    for agent in world.agents:
        assert agent.first_name
        assert agent.surname
        assert agent.name == f"{agent.first_name} {agent.surname}"
        assert not is_placeholder_name(agent.name)


def test_existing_save_migration_uses_household_surname():
    world = World(4, 4, seed=34)
    world.tiles = [[Tile("grass") for _ in range(4)] for _ in range(4)]
    world.settlement = Settlement("Test Village", 2, 2, 1, "Spring", settlement_id="settlement-1")
    household = Household(
        "household-1",
        "Willow Hearth",
        member_ids=["child-23"],
        founder_ids=["child-23"],
    )
    world.settlement.households = [household]
    child = Agent("Child 23", 1, 1, agent_id="child-23", household_id="household-1")
    world.agents = [child]

    migrate_world_names(world)

    assert household.surname == "Willow"
    assert child.surname == "Willow"
    assert child.name == f"{child.first_name} Willow"
    assert "Child 23" not in child.name
