from src.actions import _step_along_path
from src.agent import Agent
from src.intents import (
    DEPOSIT_INTENT,
    EAT_INTENT,
    HARVEST_INTENT,
    SLEEP_INTENT,
    IntentQueue,
    WALK_INTENT,
    action_intent_for,
    intent_queue_for,
    movement_intent_for,
)
from src.presentation import PresentationScene
from src.simulation_runner import SimulationRunner
from src.tile import Tile
from src.world import World


def make_world(width: int = 5, height: int = 1) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_movement_intent_is_created_from_simulation_path_state():
    agent = Agent("Ari", 1, 0, current_action="Moving to field", current_goal="Farm work")
    agent.current_target = (4, 0)
    agent.current_path = [(2, 0), (3, 0), (4, 0)]

    intent = movement_intent_for(agent)

    assert intent.kind == WALK_INTENT
    assert intent.label == "Moving to field"
    assert intent.target == (4, 0)
    assert intent.path == ((1, 0), (2, 0), (3, 0), (4, 0))


def test_action_intents_are_created_from_simulation_action_state():
    examples = [
        ("Harvesting farm", HARVEST_INTENT),
        ("Depositing", DEPOSIT_INTENT),
        ("Eating", EAT_INTENT),
        ("Sleeping", SLEEP_INTENT),
    ]

    for action, expected_kind in examples:
        intent = action_intent_for(Agent("Ari", 1, 0, current_action=action))

        assert intent.kind == expected_kind
        assert intent.label == action
        assert intent.target == (1, 0)


def test_intent_queue_places_movement_before_action_execution():
    agent = Agent("Ari", 0, 0, current_action="Harvesting farm")
    agent.current_target = (2, 0)
    agent.current_path = [(1, 0), (2, 0)]

    queue = intent_queue_for(agent)

    assert [intent.kind for intent in queue.items] == [WALK_INTENT, HARVEST_INTENT]


def test_intent_queue_replaces_with_rolling_lookahead_limit():
    first = movement_intent_for(Agent("Ari", 0, 0))
    agent = Agent("Bryn", 0, 0, current_action="Seeking water")
    agent.current_target = (4, 0)
    agent.current_path = [(1, 0), (2, 0), (3, 0), (4, 0)]
    second = movement_intent_for(agent)
    queue = IntentQueue(max_length=1)

    queue.replace([intent for intent in (first, second) if intent is not None])

    assert len(queue) == 1
    assert queue.peek() is second


def test_presentation_consumes_movement_intent_without_waiting_for_tile_updates():
    world = make_world(width=5, height=1)
    agent = Agent("Ari", 0, 0, agent_id="ari", current_action="Walking")
    agent.current_target = (4, 0)
    agent.current_path = [(1, 0), (2, 0), (3, 0), (4, 0)]
    world.agents.append(agent)
    scene = PresentationScene()

    snapshot = scene.update(world, 0.60, tiles_per_second=4.0)
    presented = snapshot.agents[0]

    assert (agent.x, agent.y) == (0, 0)
    assert presented.tile_x == 0
    assert 2 < presented.render_x < 3
    assert scene.intent_queues["ari"].peek().target == (4, 0)


def test_presentation_action_lifecycle_progresses_without_changing_simulation():
    world = make_world(width=3, height=1)
    agent = Agent("Ari", 1, 0, agent_id="ari", current_action="Harvesting")
    world.agents.append(agent)
    scene = PresentationScene()

    first = scene.update(world, 0.10, tiles_per_second=4.0).agents[0]
    second = scene.update(world, 0.80, tiles_per_second=4.0).agents[0]
    final = scene.update(world, 1.00, tiles_per_second=4.0).agents[0]

    assert first.presentation_action == "Harvesting"
    assert first.presentation_action_state == "Starting"
    assert second.presentation_action_state == "Performing"
    assert final.presentation_action_state == "Complete"
    assert final.presentation_action_progress == 1.0
    assert agent.current_action == "Harvesting"
    assert (agent.x, agent.y) == (1, 0)


def test_presentation_action_transition_resets_lifecycle():
    world = make_world(width=3, height=1)
    agent = Agent("Ari", 1, 0, agent_id="ari", current_action="Eating")
    world.agents.append(agent)
    scene = PresentationScene()

    eating = scene.update(world, 0.60, tiles_per_second=4.0).agents[0]
    agent.current_action = "Sleeping"
    sleeping = scene.update(world, 0.10, tiles_per_second=4.0).agents[0]

    assert eating.presentation_action == "Eating"
    assert eating.presentation_action_progress > sleeping.presentation_action_progress
    assert sleeping.presentation_action == "Sleeping"
    assert sleeping.presentation_action_state == "Starting"


def test_simulation_path_step_remains_authoritative_and_deterministic():
    first = make_world(width=5, height=1)
    second = make_world(width=5, height=1)
    first_agent = Agent("Ari", 0, 0)
    second_agent = Agent("Ari", 0, 0)
    first.agents.append(first_agent)
    second.agents.append(second_agent)

    _step_along_path(first_agent, first, (4, 0))
    _step_along_path(second_agent, second, (4, 0))

    assert (first_agent.x, first_agent.y) == (second_agent.x, second_agent.y)
    assert first_agent.current_path == second_agent.current_path


def test_headless_simulation_runner_does_not_require_intent_layer():
    world = make_world()
    world.agents.append(Agent("Ari", 0, 0, agent_id="ari"))
    runner = SimulationRunner(world, mode="headless")

    metrics = runner.run_ticks(2)

    assert metrics.ticks_executed == 2
    assert not hasattr(world, "intent_queues")
