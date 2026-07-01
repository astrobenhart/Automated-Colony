from __future__ import annotations

from dataclasses import dataclass, field
import os
import time
from typing import Callable, Literal

from src.config import DAYS_PER_SEASON, SEASONS, TICKS_PER_DAY
from src.profiler import profiler

SimulationMode = Literal["interactive", "headless", "validation"]


DAYS_PER_YEAR = DAYS_PER_SEASON * len(SEASONS)
INTERACTIVE_BASELINE_TICKS_PER_SECOND = 60.0


@dataclass
class SimulationRunnerMetrics:
    mode: SimulationMode
    ticks_executed: int = 0
    days_executed: int = 0
    years_executed: float = 0.0
    wall_clock_seconds: float = 0.0
    ticks_per_second: float = 0.0
    days_per_second: float = 0.0
    years_per_second: float = 0.0
    estimated_interactive_speedup: float = 0.0
    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    cpu_user_seconds: float | None = None
    cpu_system_seconds: float | None = None


@dataclass
class SimulationRunner:
    world: object
    mode: SimulationMode = "headless"
    metrics_enabled: bool = True
    disable_profiler: bool = True
    on_day: Callable[[object], None] | None = None
    on_year: Callable[[object], None] | None = None
    memory_sample_interval_ticks: int = TICKS_PER_DAY * 20
    _process: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if self.mode not in {"interactive", "headless", "validation"}:
            raise ValueError(f"Unknown simulation runner mode: {self.mode}")
        if self.mode in {"headless", "validation"}:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        self._process = optional_process()

    def run_years(self, years: int) -> SimulationRunnerMetrics:
        return self.run_days(years * DAYS_PER_YEAR)

    def run_days(self, days: int) -> SimulationRunnerMetrics:
        return self.run_ticks(days * TICKS_PER_DAY)

    def run_ticks(self, ticks: int) -> SimulationRunnerMetrics:
        start_wall = time.perf_counter()
        start_cpu = cpu_times(self._process)
        peak_memory_mb = memory_mb(self._process)
        start_day = getattr(self.world, "day", 0)
        last_day = start_day
        last_year = getattr(self.world, "year", 0)
        previous_profiler_enabled = profiler.enabled
        if self.mode in {"headless", "validation"} and self.disable_profiler:
            profiler.enabled = False

        try:
            for index in range(ticks):
                self.world.update()

                current_day = getattr(self.world, "day", last_day)
                if current_day != last_day:
                    last_day = current_day
                    if self.on_day is not None:
                        self.on_day(self.world)

                current_year = getattr(self.world, "year", last_year)
                if current_year != last_year:
                    last_year = current_year
                    if self.on_year is not None:
                        self.on_year(self.world)

                if self.metrics_enabled and self._process is not None:
                    if (index + 1) % max(1, self.memory_sample_interval_ticks) == 0:
                        peak_memory_mb = max(peak_memory_mb, memory_mb(self._process))
        finally:
            profiler.enabled = previous_profiler_enabled

        elapsed = time.perf_counter() - start_wall
        end_cpu = cpu_times(self._process)
        ticks_per_second = ticks / elapsed if elapsed > 0 else 0.0
        days_executed = max(0, getattr(self.world, "day", start_day) - start_day)
        days_per_second = days_executed / elapsed if elapsed > 0 else 0.0
        years_executed = days_executed / DAYS_PER_YEAR
        years_per_second = years_executed / elapsed if elapsed > 0 else 0.0

        current_memory_mb = memory_mb(self._process)
        return SimulationRunnerMetrics(
            mode=self.mode,
            ticks_executed=ticks,
            days_executed=days_executed,
            years_executed=years_executed,
            wall_clock_seconds=elapsed,
            ticks_per_second=ticks_per_second,
            days_per_second=days_per_second,
            years_per_second=years_per_second,
            estimated_interactive_speedup=ticks_per_second / INTERACTIVE_BASELINE_TICKS_PER_SECOND,
            peak_memory_mb=max(peak_memory_mb, current_memory_mb),
            current_memory_mb=current_memory_mb,
            cpu_user_seconds=cpu_delta(start_cpu, end_cpu, "user"),
            cpu_system_seconds=cpu_delta(start_cpu, end_cpu, "system"),
        )


def optional_process():
    try:
        import psutil
    except ImportError:  # pragma: no cover - optional diagnostics dependency
        return None
    return psutil.Process(os.getpid())


def memory_mb(process) -> float:
    if process is None:
        return 0.0
    return process.memory_info().rss / (1024 * 1024)


def cpu_times(process):
    if process is None:
        return None
    return process.cpu_times()


def cpu_delta(start, end, name: str) -> float | None:
    if start is None or end is None:
        return None
    return getattr(end, name) - getattr(start, name)
