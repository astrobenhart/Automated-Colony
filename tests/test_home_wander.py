import random

from src.actions import WanderAction, begin_idle_pause, random_tile_near_home
from src.agent import Agent
from src.config import HOME_WANDER_MAX_RADIUS, IDLE_MAX_TICKS, IDLE_MIN_TICKS
from src.settlement import Home, Settlement
from src.tile import Tile
from src.world import World, create_world


def make_world(width=12, height=12):
    world = World(width, height, seed=123)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Willowhold", width // 2, height // 2, 1, "Spring")
    world.settlement.homes = [Home(5, 5), Home(7, 5)]
    world.tile_at(5, 5).kind = "home"
    world.tile_at(7, 5).kind = "home"
    return world


def test_spawned_villagers_receive_home_tile_anchor():
    world = create_world(seed=92, agent_count=20)
    home_positions = {(home.x, home.y) for home in world.settlement.homes}

    assert home_positions
    assert all((agent.home_x, agent.home_y) in home_positions for agent in world.agents)
    assert all(3 <= agent.home_wander_radius <= HOME_WANDER_MAX_RADIUS for agent in world.agents)


def test_idle_wander_target_stays_near_home():
    world = make_world()
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5, home_wander_radius=3)
    world.agents.append(agent)

    target = random_tile_near_home(world, agent, random.Random(4))

    assert target is not None
    assert max(abs(target[0] - agent.home_x), abs(target[1] - agent.home_y)) <= agent.home_wander_radius


def test_wander_action_uses_home_anchor_not_distant_map_tiles():
    world = make_world(width=20, height=20)
    agent = Agent("Ari", 10, 10, home_x=5, home_y=5, home_wander_radius=3)
    world.agents.append(agent)

    WanderAction().execute(agent, world)

    assert agent.current_target is not None
    assert max(abs(agent.current_target[0] - agent.home_x), abs(agent.current_target[1] - agent.home_y)) <= 3


def test_idle_pause_sets_short_timer_and_no_target():
    world = make_world()
    world.tick = 20
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5)
    agent.current_target = (6, 5)
    agent.current_path = [(6, 5)]

    begin_idle_pause(agent, world, random.Random(1))

    assert agent.current_action == "Idle"
    assert agent.current_target is None
    assert agent.current_path == []
    assert world.tick + IDLE_MIN_TICKS <= agent.idle_until_tick <= world.tick + IDLE_MAX_TICKS


def test_intentional_idle_does_not_trigger_no_progress_recovery():
    world = make_world()
    world.tick = 10
    agent = Agent("Ari", 5, 5, home_x=5, home_y=5, current_action="Idle", idle_until_tick=15, no_progress_ticks=4)
    before = agent.progress_snapshot(world)

    agent.update_progress_tracking(world, before)

    assert agent.no_progress_ticks == 0
    assert agent.current_action == "Idle"
