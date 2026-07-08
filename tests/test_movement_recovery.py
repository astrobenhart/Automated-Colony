from src.actions import _step_along_path
from src.agent import Agent
from src.config import STUCK_TICK_LIMIT
from src.presentation import PresentationEngine
from src.tile import Tile
from src.world import World


def make_world(width: int, height: int) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_blocked_terrain_next_step_clears_path_and_increments_stuck_ticks():
    world = make_world(3, 1)
    world.tile_at(1, 0).kind = "mountain"
    agent = Agent("Walker", 0, 0)
    world.agents.append(agent)
    agent.current_target = (2, 0)
    agent.current_path = [(1, 0), (2, 0)]

    moved = _step_along_path(agent, world, (2, 0))

    assert not moved
    assert agent.current_path == []
    assert agent.current_target == (2, 0)
    assert agent.stuck_ticks == 1
    assert (agent.x, agent.y) == (0, 0)


def test_occupied_next_step_is_not_a_villager_movement_blocker():
    world = make_world(3, 1)
    agent = Agent("Walker", 0, 0)
    blocker = Agent("Blocker", 1, 0)
    world.agents.extend([agent, blocker])
    agent.current_target = (2, 0)
    agent.current_path = [(1, 0), (2, 0)]

    moved = _step_along_path(agent, world, (2, 0))

    assert moved
    assert agent.stuck_ticks == 0
    assert (agent.x, agent.y) == (1, 0)


def test_stuck_agent_eventually_clears_path_and_target():
    world = make_world(3, 1)
    world.tile_at(1, 0).kind = "mountain"
    agent = Agent("Walker", 0, 0)
    world.agents.append(agent)

    for _ in range(STUCK_TICK_LIMIT):
        _step_along_path(agent, world, (2, 0))

    assert agent.current_path == []
    assert agent.current_target is None
    assert agent.stuck_ticks == STUCK_TICK_LIMIT
    assert (agent.x, agent.y) == (0, 0)


def test_successful_movement_resets_stuck_ticks():
    world = make_world(3, 1)
    agent = Agent("Walker", 0, 0, stuck_ticks=2)
    world.agents.append(agent)

    moved = _step_along_path(agent, world, (2, 0))

    assert moved
    assert agent.stuck_ticks == 0
    assert (agent.x, agent.y) == (1, 0)
    assert world.tile_at(1, 0).foot_traffic == 1


def test_path_step_updates_simulation_position_for_presentation_to_observe():
    world = make_world(4, 1)
    agent = Agent("Walker", 0, 0)
    world.agents.append(agent)
    presentation = PresentationEngine()
    presentation.sync_world(world)

    moved = _step_along_path(agent, world, (3, 0))
    snapshot = presentation.update(world, 0.05, tiles_per_second=4.0)
    presented_agent = snapshot.agents[0]

    assert moved
    assert (agent.x, agent.y) == (1, 0)
    assert agent.current_path == [(2, 0), (3, 0)]
    assert presented_agent.tile_x == 1
    assert presented_agent.tile_y == 0
    assert 0 < presented_agent.render_x < 1
    assert presented_agent.render_y == 0
