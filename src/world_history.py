from dataclasses import dataclass, field


ENVIRONMENT = "ENVIRONMENT"
SEASON = "SEASON"
WILDLIFE = "WILDLIFE"
SETTLEMENT = "SETTLEMENT"

HISTORY_CATEGORIES = {
    ENVIRONMENT,
    SEASON,
    WILDLIFE,
    SETTLEMENT,
}


@dataclass(frozen=True)
class HistoryEntry:
    day: int
    year: int
    season: str
    category: str
    title: str
    description: str


@dataclass
class WorldHistory:
    entries: list[HistoryEntry] = field(default_factory=list)

    def record(
        self,
        *,
        day: int,
        year: int,
        season: str,
        category: str,
        title: str,
        description: str,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            day=day,
            year=year,
            season=season,
            category=category,
            title=title,
            description=description,
        )
        self.entries.append(entry)
        return entry

    def recent(self, limit: int):
        if limit <= 0:
            return []
        return self.entries[-limit:]

    def by_category(self, category: str):
        return [entry for entry in self.entries if entry.category == category]

    def count(self) -> int:
        return len(self.entries)
