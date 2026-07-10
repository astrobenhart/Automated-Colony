from src.agent import Agent
from src.pathfinding import find_path
from src.presentation import PresentationAgent, PresentationEngine, PresentationScene, PresentationSnapshot, PresentationTime
from src.simulation_runner import SimulationRunner
from src.tile import Tile
from src.world import World


def make_world(width: int = 4, height: int = 4) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_presentation_snapshot_mirrors_living_simulation_agents():
    world = make_world()
    living = Agent("Ari Stone", 1, 2, agent_id="ari")
    dead = Agent("Gone Vale", 2, 2, agent_id="gone", alive=False)
    world.agents.extend([living, dead])

    engine = PresentationEngine()
    snapshot = engine.snapshot_world(world)

    assert isinstance(snapshot, PresentationSnapshot)
    assert len(snapshot.agents) == 1
    agent = snapshot.agents[0]
    assert agent.agent_id == "ari"
    assert agent.tile_x == 1
    assert agent.tile_y == 2
    assert agent.render_x == 1
    assert agent.render_y == 2


def test_presentation_scene_creates_scene_root_and_owns_agents():
    world = make_world()
    agent = Agent("Ari Stone", 1, 2, agent_id="ari")
    world.agents.append(agent)

    scene = PresentationScene()
    snapshot = scene.snapshot_world(world)

    assert isinstance(snapshot, PresentationSnapshot)
    assert "agents" in scene.render_order
    assert "ari" in scene.agents
    assert scene.agents["ari"].agent_id == "ari"
    assert snapshot.render_order == scene.render_order


def test_presentation_scene_tracks_frame_state_without_changing_world():
    world = make_world()
    agent = Agent("Ari Stone", 0, 0, agent_id="ari")
    world.agents.append(agent)
    scene = PresentationScene()
    scene.sync_world(world)

    snapshot = scene.update(world, 0.25, tiles_per_second=4.0)

    assert scene.presentation_time.frame_index == 1
    assert scene.presentation_time.delta_seconds == 0.25
    assert scene.presentation_time.elapsed_seconds == 0.25
    assert snapshot.frame_index == 1
    assert snapshot.delta_seconds == 0.25
    assert snapshot.elapsed_seconds == 0.25
    assert (agent.x, agent.y) == (0, 0)


def test_presentation_time_advances_independently_from_simulation_ticks():
    world = make_world()
    world.agents.append(Agent("Ari Stone", 0, 0, agent_id="ari"))
    scene = PresentationScene()

    scene.update(world, 0.10, tiles_per_second=4.0)
    scene.update(world, 0.15, tiles_per_second=4.0)

    assert world.tick == 0
    assert scene.presentation_time.frame_index == 2
    assert round(scene.presentation_time.elapsed_seconds, 2) == 0.25


def test_presentation_time_pause_stops_elapsed_time_and_interpolation():
    world = make_world()
    agent = Agent("Ari Stone", 0, 0, agent_id="ari")
    world.agents.append(agent)
    scene = PresentationScene()
    scene.sync_world(world)
    agent.x = 1

    snapshot = scene.update(world, 0.5, tiles_per_second=4.0, paused=True)

    presented = snapshot.agents[0]
    assert scene.presentation_time.paused
    assert scene.presentation_time.frame_index == 1
    assert scene.presentation_time.elapsed_seconds == 0
    assert scene.presentation_time.delta_seconds == 0
    assert presented.render_x == 0
    assert presented.tile_x == 1


def test_presentation_time_supports_scale_and_interpolation_alpha():
    clock = PresentationTime()

    clock.advance(0.5, time_scale=0.5, interpolation_alpha=1.25)

    assert clock.frame_index == 1
    assert clock.delta_seconds == 0.25
    assert clock.elapsed_seconds == 0.25
    assert clock.interpolation_alpha == 1.0
    assert clock.time_scale == 0.5


def test_presentation_interpolates_agent_position_without_changing_simulation():
    world = make_world()
    agent = Agent("Ari Stone", 0, 0, agent_id="ari")
    world.agents.append(agent)
    engine = PresentationEngine()
    engine.sync_world(world)

    agent.x = 2
    snapshot = engine.update(world, 0.10, tiles_per_second=4.0)

    presented = snapshot.agents[0]
    assert snapshot.delta_seconds == 0.10
    assert (agent.x, agent.y) == (2, 0)
    assert presented.tile_x == 2
    assert presented.tile_y == 0
    assert 0 < presented.render_x < 2
    assert presented.render_y == 0


def test_presentation_route_preserves_unreached_waypoints_when_intent_advances():
    world = make_world(width=5, height=1)
    agent = Agent("Ari Stone", 0, 0, agent_id="ari", current_action="Walking")
    agent.current_target = (4, 0)
    agent.current_path = [(1, 0), (2, 0), (3, 0), (4, 0)]
    world.agents.append(agent)
    scene = PresentationScene()

    scene.update(world, 0.0, tiles_per_second=4.0)
    presentation_agent = scene.agents["ari"]

    agent.x = 2
    agent.current_path = [(3, 0), (4, 0)]
    scene.update(world, 0.0, tiles_per_second=4.0)

    assert presentation_agent.presentation_route == ((1, 0), (2, 0), (3, 0), (4, 0))
    assert (presentation_agent.target_x, presentation_agent.target_y) == (1.0, 0.0)
    assert presentation_agent.route_recovery_reason is None


def test_presentation_route_merges_future_intent_without_duplicate_waypoints():
    world = make_world(width=6, height=1)
    agent = Agent("Ari Stone", 0, 0, agent_id="ari", current_action="Walking")
    agent.current_target = (3, 0)
    agent.current_path = [(1, 0), (2, 0), (3, 0)]
    world.agents.append(agent)
    scene = PresentationScene()

    scene.update(world, 0.0, tiles_per_second=4.0)
    presentation_agent = scene.agents["ari"]

    agent.x = 2
    agent.current_target = (5, 0)
    agent.current_path = [(3, 0), (4, 0), (5, 0)]
    scene.update(world, 0.0, tiles_per_second=4.0)

    assert presentation_agent.presentation_route == ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0))
    assert presentation_agent.presentation_route.count((3, 0)) == 1


def test_presentation_route_respects_water_barrier_when_simulation_advances_ahead():
    world = make_world(width=5, height=5)
    for y in range(1, 5):
        world.tiles[y][2] = Tile("water")

    target = (4, 2)
    route = find_path(world, (0, 2), target)
    agent = Agent("Ari Stone", 0, 2, agent_id="ari", current_action="Walking")
    agent.current_target = target
    agent.current_path = list(route)
    world.agents.append(agent)
    scene = PresentationScene()

    scene.update(world, 0.0, tiles_per_second=4.0)
    presentation_agent = scene.agents["ari"]

    agent.x, agent.y = (4, 1)
    agent.current_path = [(4, 2)]
    scene.update(world, 0.0, tiles_per_second=4.0)

    assert presentation_agent.presentation_route[: len(route)] == tuple(route)
    assert (presentation_agent.target_x, presentation_agent.target_y) == tuple(float(value) for value in route[0])
    for waypoint in presentation_agent.presentation_route:
        assert world.tile_at(*waypoint).walkable
    assert presentation_agent.route_recovery_reason is None


def test_presentation_route_recovery_is_explicit_when_route_starts_too_far_ahead():
    world = make_world(width=5, height=5)
    for y in range(1, 5):
        world.tiles[y][2] = Tile("water")

    visual_agent = Agent("Ari Stone", 0, 2, agent_id="ari", current_action="Walking")
    agent = Agent("Ari Stone", 4, 1, agent_id="ari", current_action="Walking")
    agent.current_target = (4, 2)
    agent.current_path = [(4, 2)]
    world.agents.append(agent)
    scene = PresentationScene()
    scene.agents["ari"] = PresentationAgent.from_agent(visual_agent)

    scene.update(world, 0.0, tiles_per_second=4.0)
    presentation_agent = scene.agents["ari"]

    assert presentation_agent.route_recovery_reason == "route_started_ahead_of_render"
    assert (presentation_agent.render_x, presentation_agent.render_y) == (4.0, 1.0)
    assert (presentation_agent.target_x, presentation_agent.target_y) == (4.0, 2.0)


def test_presentation_engine_remains_scene_compatible():
    engine = PresentationEngine()

    assert isinstance(engine, PresentationScene)


def test_presentation_finishes_interpolation_at_simulation_position():
    world = make_world()
    agent = Agent("Ari Stone", 0, 0, agent_id="ari")
    world.agents.append(agent)
    engine = PresentationEngine()
    engine.sync_world(world)

    agent.x = 1
    snapshot = engine.update(world, 1.0, tiles_per_second=4.0)

    presented = snapshot.agents[0]
    assert presented.render_x == 1
    assert presented.render_y == 0


def test_headless_simulation_runner_does_not_require_presentation_engine():
    world = make_world()
    world.agents.append(Agent("Ari Stone", 1, 1, agent_id="ari"))
    runner = SimulationRunner(world, mode="headless")

    metrics = runner.run_ticks(3)

    assert metrics.ticks_executed == 3
    assert not hasattr(world, "presentation_engine")


def test_presentation_removes_dead_agents_from_snapshots():
    world = make_world()
    agent = Agent("Ari Stone", 1, 1, agent_id="ari")
    world.agents.append(agent)
    engine = PresentationEngine()
    engine.sync_world(world)

    agent.alive = False
    snapshot = engine.update(world, 0.1, tiles_per_second=4.0)

    assert snapshot.agents == ()
    assert engine.agents == {}
