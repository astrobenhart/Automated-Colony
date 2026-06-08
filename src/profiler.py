from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter


@dataclass
class ProfileStat:
    calls: int = 0
    total_seconds: float = 0.0

    @property
    def average_seconds(self) -> float:
        if self.calls == 0:
            return 0.0
        return self.total_seconds / self.calls


class Profiler:
    def __init__(self):
        self.enabled = True
        self.stats: dict[str, ProfileStat] = {}

    def reset(self):
        self.stats.clear()

    @contextmanager
    def time(self, name: str):
        if not self.enabled:
            yield
            return

        start = perf_counter()
        try:
            yield
        finally:
            elapsed = perf_counter() - start
            stat = self.stats.setdefault(name, ProfileStat())
            stat.calls += 1
            stat.total_seconds += elapsed

    def report(self) -> list[tuple[str, int, float, float]]:
        rows = [
            (name, stat.calls, stat.average_seconds, stat.total_seconds)
            for name, stat in self.stats.items()
        ]
        return sorted(rows, key=lambda row: row[3], reverse=True)


profiler = Profiler()
