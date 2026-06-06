from src.actions import _step_along_path
from src.agent import Agent
from src.config import STUCK_TICK_LIMIT
from src.tile import Tile
from src.world import World


def make_world(width: int, height: int) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_blocked_next_step_clears_path_and_increments_stuck_ticks():
    world = make_world(3, 1)
    agent = Agent("Walker", 0, 0)
    blocker = Agent("Blocker", 1, 0)
    world.agents.extend([agent, blocker])
    agent.current_target = (2, 0)
    agent.current_path = [(1, 0), (2, 0)]

    moved = _step_along_path(agent, world, (2, 0))

    assert not moved
    assert agent.current_path == []
    assert agent.current_target == (2, 0)
    assert agent.stuck_ticks == 1
    assert (agent.x, agent.y) == (0, 0)


def test_stuck_agent_eventually_clears_path_and_target():
    world = make_world(3, 1)
    agent = Agent("Walker", 0, 0)
    blocker = Agent("Blocker", 1, 0)
    world.agents.extend([agent, blocker])

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
