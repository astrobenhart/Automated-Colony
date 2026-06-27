from src.config import TICKS_PER_DAY
from src.simulation_runner import SimulationRunner


class FakeWorld:
    def __init__(self):
        self.day = 1
        self.year = 1
        self.update_calls = 0
        self.advance_day_calls = 0

    def update(self):
        self.update_calls += 1
        if self.update_calls % TICKS_PER_DAY == 0:
            self.day += 1

    def advance_day(self):  # pragma: no cover - must never be used by the runner
        self.advance_day_calls += 1
        raise AssertionError("SimulationRunner must use world.update(), not advance_day().")


def test_headless_runner_executes_every_tick_through_world_update():
    world = FakeWorld()
    runner = SimulationRunner(world, mode="headless")

    metrics = runner.run_days(2)

    assert world.update_calls == TICKS_PER_DAY * 2
    assert world.advance_day_calls == 0
    assert world.day == 3
    assert metrics.ticks_executed == TICKS_PER_DAY * 2
    assert metrics.days_executed == 2
    assert metrics.ticks_per_second > 0


def test_runner_day_callback_observes_production_day_changes():
    world = FakeWorld()
    observed_days = []
    runner = SimulationRunner(world, mode="validation", on_day=lambda updated_world: observed_days.append(updated_world.day))

    runner.run_ticks(TICKS_PER_DAY * 3)

    assert observed_days == [2, 3, 4]
