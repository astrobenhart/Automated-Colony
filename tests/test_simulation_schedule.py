from src.actions import Action
from src.agent import Agent
from src.config import DECISION_INTERVAL_TICKS, MAX_UPDATES_PER_TICK, TICKS_PER_DAY, TICKS_PER_HOUR
from src.tile import Tile
from src.world import World


def make_world(width=5, height=5):
    world = World(width, height, seed=123)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_settlement_metrics_run_on_daily_schedule_not_every_tick():
    world = make_world()
    calls = {"metrics": 0}

    def count_metrics():
        calls["metrics"] += 1

    world.run_daily_settlement_updates = count_metrics

    world.update()
    assert calls["metrics"] == 0

    world.tick = TICKS_PER_DAY - 1
    world.update()
    assert calls["metrics"] == 1


def test_day_length_config_uses_100_ticks_with_clean_hourly_division():
    assert TICKS_PER_DAY == 100
    assert TICKS_PER_HOUR == 10
    assert TICKS_PER_DAY % TICKS_PER_HOUR == 0


def test_wildlife_updates_hourly_and_on_daily_tick(monkeypatch):
    world = make_world()
    calls = {"wildlife": 0}

    def count_wildlife(target_world, rng):
        assert target_world is world
        calls["wildlife"] += 1

    monkeypatch.setattr("src.world.update_wildlife", count_wildlife)

    for _ in range(TICKS_PER_HOUR - 1):
        world.update()
    assert calls["wildlife"] == 0

    world.update()
    assert calls["wildlife"] == 1

    world.tick = TICKS_PER_DAY - 1
    world.update()
    assert calls["wildlife"] == 2


def test_agent_decision_is_cached_between_decision_intervals():
    world = make_world()
    agent = Agent("Ari", 2, 2)
    world.agents.append(agent)
    calls = {"decisions": 0}

    def choose_action(target_world):
        assert target_world is world
        calls["decisions"] += 1
        return Action()

    agent.choose_action = choose_action

    for _ in range(DECISION_INTERVAL_TICKS):
        world.update()

    assert calls["decisions"] == 1

    world.update()
    assert calls["decisions"] == 2


def test_invalid_cached_action_triggers_fresh_decision_before_interval():
    world = make_world()
    agent = Agent("Ari", 2, 2)
    world.agents.append(agent)
    calls = {"decisions": 0}

    class OneTickAction(Action):
        def __init__(self):
            self.used = False

        def can_do(self, target_agent, target_world):
            return not self.used

        def execute(self, target_agent, target_world):
            self.used = True
            super().execute(target_agent, target_world)

    def choose_action(target_world):
        calls["decisions"] += 1
        return OneTickAction()

    agent.choose_action = choose_action

    world.update()
    world.update()

    assert calls["decisions"] == 2


def test_world_updates_limited_rotating_villager_batch_per_tick():
    world = make_world(width=12, height=12)
    world.agents = [Agent(f"A{index}", index % 12, index // 12) for index in range(MAX_UPDATES_PER_TICK + 7)]
    updated = []

    def update_villager(agent):
        updated.append(agent.name)

    world.update_villager = update_villager

    first_count = world.update_villagers_for_tick()
    second_count = world.update_villagers_for_tick()

    assert first_count == MAX_UPDATES_PER_TICK
    assert second_count == MAX_UPDATES_PER_TICK
    assert updated[:MAX_UPDATES_PER_TICK] == [f"A{index}" for index in range(MAX_UPDATES_PER_TICK)]
    assert updated[MAX_UPDATES_PER_TICK:] == [
        f"A{index}" for index in range(MAX_UPDATES_PER_TICK, MAX_UPDATES_PER_TICK * 2)
    ]
    assert world.villager_update_cursor == MAX_UPDATES_PER_TICK * 2
