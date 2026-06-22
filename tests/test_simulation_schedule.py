from src.actions import Action
from src.agent import Agent
from src.config import DECISION_INTERVAL_TICKS, HUNGER_RATE, MAX_UPDATES_PER_TICK, TICKS_PER_DAY, TICKS_PER_HOUR
from src.simulation_lod import LOD_1_TASKS, LOD_2_NEEDS, LOD_3_SOCIAL, LOD_4_PLANNING, LOD_5_HISTORY
from src.tile import Tile
from src.world import World, create_world
from src.task_behavior import STATE_DRINKING, STATE_HANDLING_NEED


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


def test_needs_update_hourly_instead_of_inside_each_villager_tick():
    world = make_world(width=12, height=12)
    world.agents = [Agent(f"A{index}", index % 12, index // 12) for index in range(MAX_UPDATES_PER_TICK + 3)]

    for _ in range(TICKS_PER_HOUR - 1):
        world.update()

    assert all(agent.hunger == 0 for agent in world.agents)
    assert all(agent.thirst == 0 for agent in world.agents)
    assert all(agent.fatigue == 0 for agent in world.agents)

    world.update()

    expected = HUNGER_RATE * TICKS_PER_HOUR * MAX_UPDATES_PER_TICK / len(world.agents)
    assert all(agent.hunger == expected for agent in world.agents)
    assert all(agent.thirst == expected for agent in world.agents)
    assert all(agent.fatigue == expected for agent in world.agents)


def test_lod_needs_match_pre_lod_effective_daily_pressure():
    world = make_world(width=12, height=12)
    world.agents = [Agent(f"A{index}", index % 12, index // 12) for index in range(45)]
    hours_per_day = TICKS_PER_DAY // TICKS_PER_HOUR
    expected_daily_increase = HUNGER_RATE * TICKS_PER_DAY * MAX_UPDATES_PER_TICK / len(world.agents)

    for _ in range(hours_per_day):
        world.update_needs_for_lod(TICKS_PER_HOUR)

    assert all(abs(agent.hunger - expected_daily_increase) < 0.000001 for agent in world.agents)
    assert all(abs(agent.thirst - expected_daily_increase) < 0.000001 for agent in world.agents)
    assert all(abs(agent.fatigue - expected_daily_increase) < 0.000001 for agent in world.agents)


def test_lod_needs_do_not_mass_kill_default_start_by_day_three():
    world = create_world(seed=59)

    for _ in range(TICKS_PER_DAY * 3):
        world.update()

    deaths_by_day_three = len(world.death_records)
    assert deaths_by_day_three < 5
    assert len(world.living_agents()) >= 40


def test_pending_survival_actions_resolve_before_death_checks():
    world = make_world()
    drinking = Agent(
        "Ari",
        2,
        2,
        thirst=99.5,
        water=1,
        task_state=STATE_DRINKING,
        task_timer=1,
        current_goal="Handle thirst",
    )
    eating = Agent(
        "Bryn",
        2,
        3,
        hunger=99.5,
        food=1,
        task_state=STATE_HANDLING_NEED,
        task_timer=1,
        current_goal="Handle hunger",
    )
    world.agents = [drinking, eating]

    world.update_needs_for_lod(TICKS_PER_HOUR)
    assert drinking.alive
    assert eating.alive

    world.update_villager(drinking)
    world.update_villager(eating)

    assert drinking.alive
    assert drinking.thirst == 0
    assert drinking.water == 0
    assert eating.alive
    assert eating.hunger < 100
    assert eating.food == 0
    assert world.death_records == []


def test_lod_profile_tracks_counts_and_costs():
    world = make_world(width=12, height=12)
    world.agents = [Agent(f"A{index}", index % 12, index // 12) for index in range(3)]

    world.update()
    world.tick = TICKS_PER_HOUR - 1
    world.update()

    stats = world.lod_stats
    assert stats[LOD_1_TASKS].calls == 2
    assert stats[LOD_2_NEEDS].calls == 1
    assert stats[LOD_1_TASKS].average_seconds >= 0
    assert any(row[0] == LOD_1_TASKS for row in world.lod_report())


def test_daily_lod_tiers_are_counted(monkeypatch):
    world = make_world(width=12, height=12)

    monkeypatch.setattr("src.world.update_social_memory", lambda target_world: None)
    monkeypatch.setattr("src.world.update_household_familiarity", lambda target_world: None)
    monkeypatch.setattr("src.world.update_influence_peaks", lambda target_world: None)
    monkeypatch.setattr("src.world.expire_remembrances", lambda target_world: None)

    world.run_daily_updates()

    assert world.lod_stats[LOD_2_NEEDS].calls == 1
    assert world.lod_stats[LOD_3_SOCIAL].calls == 1
    assert world.lod_stats[LOD_4_PLANNING].calls >= 2
    assert world.lod_stats[LOD_5_HISTORY].calls == 1


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
