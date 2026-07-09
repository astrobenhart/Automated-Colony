from src.agent import Agent
from src.presentation import PresentationEngine, PresentationScene, PresentationSnapshot
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

    assert scene.frame_state.frame_index == 1
    assert scene.frame_state.time_delta == 0.25
    assert snapshot.frame_index == 1
    assert (agent.x, agent.y) == (0, 0)


def test_presentation_interpolates_agent_position_without_changing_simulation():
    world = make_world()
    agent = Agent("Ari Stone", 0, 0, agent_id="ari")
    world.agents.append(agent)
    engine = PresentationEngine()
    engine.sync_world(world)

    agent.x = 2
    snapshot = engine.update(world, 0.10, tiles_per_second=4.0)

    presented = snapshot.agents[0]
    assert (agent.x, agent.y) == (2, 0)
    assert presented.tile_x == 2
    assert presented.tile_y == 0
    assert 0 < presented.render_x < 2
    assert presented.render_y == 0


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
