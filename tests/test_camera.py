from src.agent import Agent
from src.presentation import ObserverCamera, PresentationScene
from src.simulation_runner import SimulationRunner
from src.tile import Tile
from src.world import World


def make_world(width: int = 12, height: int = 10) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_observer_camera_creation_and_scene_ownership():
    scene = PresentationScene()

    scene.configure_camera(
        world_width=40,
        world_height=30,
        viewport_width=10,
        viewport_height=8,
    )

    assert isinstance(scene.observer_camera, ObserverCamera)
    assert scene.camera is scene.observer_camera
    assert scene.snapshot().camera.viewport_width == 10
    assert scene.snapshot().camera.viewport_height == 8


def test_observer_camera_world_space_coordinate_conversion():
    camera = ObserverCamera()
    camera.configure_viewport(
        world_width=40,
        world_height=30,
        viewport_width=10,
        viewport_height=8,
    )
    camera.set_position(3.5, 2.25, snap=True)

    assert camera.world_to_screen(4.5, 3.25, tile_size=16) == (16.0, 16.0)
    assert camera.screen_to_world(16, 16, tile_size=16) == (4.5, 3.25)
    assert camera.screen_to_tile(17, 17, tile_size=16) == (4, 3)


def test_observer_camera_interpolates_toward_target_with_presentation_time():
    world = make_world(width=40, height=30)
    scene = PresentationScene()
    scene.configure_camera(
        world_width=world.width,
        world_height=world.height,
        viewport_width=10,
        viewport_height=8,
    )
    scene.observer_camera.set_position(0, 0, snap=True)
    scene.observer_camera.pan_by(8, 0)

    scene.update(world, 0.05, tiles_per_second=4.0)

    assert 0 < scene.observer_camera.world_x < 8
    assert scene.observer_camera.target_x == 8


def test_observer_camera_snapshot_mirrors_scene_camera():
    world = make_world(width=40, height=30)
    scene = PresentationScene()
    scene.configure_camera(
        world_width=world.width,
        world_height=world.height,
        viewport_width=10,
        viewport_height=8,
    )
    scene.observer_camera.set_position(5, 4, snap=True)

    snapshot = scene.update(world, 0.1, tiles_per_second=4.0)

    assert snapshot.camera.world_x == 5
    assert snapshot.camera.world_y == 4
    assert snapshot.camera.target_x == 5
    assert snapshot.camera.target_y == 4


def test_headless_simulation_runner_does_not_require_observer_camera():
    world = make_world()
    world.agents.append(Agent("Ari Stone", 1, 1, agent_id="ari"))
    runner = SimulationRunner(world, mode="headless")

    metrics = runner.run_ticks(2)

    assert metrics.ticks_executed == 2
    assert not hasattr(world, "observer_camera")
