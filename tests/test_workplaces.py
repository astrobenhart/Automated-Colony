from src.workplace import FARM, STORAGE, VILLAGE_CENTER, WORKSHOP, WORKPLACE_TYPES
from src.village_paths import is_path_like
from src.world import create_world


def test_starting_settlement_registers_core_workplaces():
    world = create_world(seed=141, agent_count=0)
    workplaces = world.settlement.workplaces
    workplace_types = {workplace.workplace_type for workplace in workplaces}

    assert {STORAGE, FARM, WORKSHOP, VILLAGE_CENTER} <= workplace_types
    assert all(workplace.workplace_id for workplace in workplaces)
    assert all(workplace.workplace_type in WORKPLACE_TYPES for workplace in workplaces)
    assert all(workplace.capacity > 0 for workplace in workplaces)


def test_workplace_placeholders_do_not_create_productive_farms_at_start():
    world = create_world(seed=142, agent_count=0)
    farm_workplaces = world.settlement.workplaces_for_type(FARM)

    assert farm_workplaces
    assert world.settlement.farm_plots == []
    assert all(world.farm_at(x, y) is None for workplace in farm_workplaces for x, y in workplace.tiles)


def test_workplace_positions_are_queryable_and_in_bounds():
    world = create_world(seed=143, agent_count=0)

    for workplace in world.settlement.workplaces:
        assert 0 <= workplace.x < world.width
        assert 0 <= workplace.y < world.height
        assert workplace.tiles
        for x, y in workplace.tiles:
            assert 0 <= x < world.width
            assert 0 <= y < world.height
            assert world.workplace_at(x, y) == workplace


def test_spawned_villagers_can_reference_registered_workplaces():
    world = create_world(seed=144, agent_count=20)
    workplace_ids = {workplace.workplace_id for workplace in world.settlement.workplaces}
    assigned_agents = [agent for agent in world.agents if agent.workplace_id is not None]

    assert assigned_agents
    assert all(agent.workplace_id in workplace_ids for agent in assigned_agents)
    for workplace in world.settlement.workplaces:
        assert len(workplace.assigned_workers) <= workplace.capacity


def test_seeded_paths_connect_to_workplace_areas():
    world = create_world(seed=145, agent_count=0)
    path_tiles = {
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if is_path_like(tile.kind)
    }

    assert path_tiles
    for workplace in world.settlement.workplaces:
        assert any(
            max(abs(px - tx), abs(py - ty)) <= 1
            for tx, ty in workplace.tiles
            for px, py in path_tiles
        )
